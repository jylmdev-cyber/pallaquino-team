"""Parallel durable jobs, fenced leases, resource reservations and reviewed merges."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import datetime as dt
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

from . import adapters, governance, quality, routing, store
from .. import checkpoints, memory, orchestration
from ..common import KitError, atomic_write, http_json, is_sensitive, now, read_json, redact, redact_data, safe_path, write_json
from ..context_format import digest


def file_hash(root, relative):
    path = safe_path(root, relative)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def resource_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise KitError('Use rutas relativas POSIX de archivos.')
    root = Path(root).resolve()
    path = safe_path(root, relative)
    relative = path.relative_to(root).as_posix()
    if relative == '.' or any(part.startswith('.') or part in {'project-memory', 'node_modules', 'build', 'dist'} for part in Path(relative).parts) or is_sensitive(path):
        raise KitError('Los trabajos no pueden escribir/leer memoria, políticas, credenciales o carpetas internas: ' + relative)
    if any(re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I) or part.rstrip(' .') != part for part in Path(relative).parts):
        raise KitError('Nombre no portable o reservado en alcance.')
    if path.exists() and (not path.is_file() or path.is_symlink()):
        raise KitError('El alcance debe declarar archivos regulares, no carpetas/enlaces.')
    return relative


def validate_command(command):
    if not isinstance(command, dict) or set(command) != {'tool', 'args'} or not isinstance(command['tool'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', command['tool']) or not isinstance(command['args'], list) or not command['args'] or any(not isinstance(a, str) or '\x00' in a for a in command['args']):
        raise KitError('Comando requiere herramienta declarada y args estructurados no vacíos.')


def normalize_spec(root, proposed):
    defaults = {'depends_on': [], 'reads': [], 'writes': [], 'command': None, 'environment': 'development',
        'isolation': 'native', 'reviewed_code': False, 'image': None, 'timeout_seconds': 30,
        'max_attempts': 1, 'budget_units': 1, 'gates': [], 'repair': None, 'memory_task': None,
        'model_requirements': None, 'prompt_file': None, 'agent':'auto', 'agent_selection':None, 'skills':[]}
    required = {'id', 'title', 'acceptance'}
    if not isinstance(proposed, dict) or not required <= set(proposed) or set(proposed) - required - set(defaults):
        raise KitError('Contrato de trabajo inválido.')
    spec = {**deepcopy(defaults), **deepcopy(proposed)}
    if not isinstance(spec['id'], str) or not re.fullmatch(r'J-[a-zA-Z0-9_-]{1,64}', spec['id']):
        raise KitError('ID de trabajo debe comenzar por J-.')
    if any(not isinstance(spec[k], str) or not spec[k].strip() for k in ('title', 'acceptance')):
        raise KitError('Agente, título y aceptación requeridos.')
    if spec['agent'] == 'auto':
        proposal = orchestration.plan(root, spec['title'] + ' ' + spec['acceptance'])
        candidates = [step['role'] for step in proposal['steps']]
        priority = ['migration-engineer','frontend-engineer','backend-engineer','database-architect','devops-engineer']
        spec['agent'] = next((role for role in priority if role in candidates), candidates[0])
        spec['agent_selection'] = {'method':'local-rules','candidates':candidates,'selected':spec['agent']}
    installed = store.load(root)['extensions']
    if spec['agent'] not in set(memory.agents()) | {m['id'] for m in installed if m['kind']=='agent'}:
        raise KitError('Agente no declarado o no instalado.')
    known_skills = {skill for contract in memory.agents().values() for skill in contract['skills']} | {m['id'] for m in installed if m['kind']=='skill'}
    if not isinstance(spec['skills'],list) or any(not isinstance(skill,str) or skill not in known_skills for skill in spec['skills']):
        raise KitError('Skill no declarada o no instalada.')
    for key in ('reads', 'writes', 'depends_on'):
        if not isinstance(spec[key], list) or any(not isinstance(v, str) for v in spec[key]) or len(spec[key]) != len(set(spec[key])):
            raise KitError('Lista inválida o duplicada: ' + key)
    spec['reads'] = [resource_path(root, p) for p in spec['reads']]
    spec['writes'] = [resource_path(root, p) for p in spec['writes']]
    for key in ('reads', 'writes'):
        if len({p.casefold() for p in spec[key]}) != len(spec[key]):
            raise KitError('Colisión de rutas normalizadas en ' + key)
    if any(overlap(a, b) for index, a in enumerate(spec['writes']) for b in spec['writes'][index+1:]):
        raise KitError('Salidas con rutas superpuestas dentro del trabajo.')
    if not spec['writes']:
        raise KitError('Se requiere declarar al menos un archivo de salida.')
    for key in ('timeout_seconds', 'max_attempts'):
        if type(spec[key]) is not int or spec[key] < 1:
            raise KitError('Límite inválido: ' + key)
    if type(spec['budget_units']) not in (int, float) or not math.isfinite(spec['budget_units']) or spec['budget_units'] < 0:
        raise KitError('Unidades de presupuesto inválidas.')
    if spec['environment'] not in {'development', 'test', 'staging', 'production'} or spec['isolation'] not in {'native', 'container'} or type(spec['reviewed_code']) is not bool:
        raise KitError('Entorno/aislamiento inválido.')
    if not spec['model_requirements']:
        validate_command(spec['command'])
    elif spec['command'] is not None or not isinstance(spec['model_requirements'], dict) or len(spec['writes']) != 1 or spec['prompt_file'] not in spec['reads']:
        raise KitError('Modelo requiere un prompt declarado en reads y una sola salida; sin command.')
    if spec['repair'] is not None:
        validate_command(spec['repair'])
    if spec['gates']:
        quality.validate_gates(spec['gates'])
    if redact_data(spec) != spec:
        raise KitError('Posible secreto dentro del contrato; usar referencias seguras, no credenciales.')
    settings = governance.policy(root)
    available = adapters.catalog(root)
    used = [spec['command'], spec['repair']] + [g for g in spec['gates'] + quality.project_gates(root) if g['kind'] == 'command']
    for command in (c for c in used if c):
        if command['tool'] not in settings['allowed_tools'] or command['tool'] not in available:
            raise KitError('Herramienta no instalada o no permitida: ' + command['tool'])
    if spec['max_attempts'] > settings['max_attempts'] or spec['timeout_seconds'] > settings['max_timeout_seconds']:
        raise KitError('Límites del trabajo exceden la política del proyecto.')
    if spec['isolation'] == 'native' and (not settings['native_reviewed_code'] or not spec['reviewed_code']):
        raise KitError('Código no revisado requiere contenedor con imagen aprobada; no se ejecutará nativamente.')
    if spec['isolation'] == 'container' and spec['image'] not in settings['allowed_container_images']:
        raise KitError('Imagen de contenedor no aprobada por digest.')
    return spec


def execution_resource(root, spec, base=None, gates=None):
    return spec['id'] + ':' + digest({'spec': spec, 'gates': quality.project_gates(root) if gates is None else gates,
        'inputs_and_base': {path: file_hash(root, path) for path in sorted(set(spec['reads'] + spec['writes']))} if base is None else base,
        'extensions': store.load(root)['extensions']})


def add_job(root, proposed, approval=None):
    spec = normalize_spec(root, proposed)
    with store.transaction(root) as state:
        governance.authorize(root, 'plan.write', spec['id'], approval)
        by_id = {job['id']: job for job in state['jobs']}
        if spec['id'] in by_id:
            if by_id[spec['id']]['spec'] == spec:
                return {'id': spec['id'], 'already_added': True, 'execution_resource': execution_resource(root, spec)}
            raise KitError('Trabajo existente con otro contrato.')
        if not set(spec['depends_on']) <= set(by_id):
            raise KitError('Las dependencias deben existir; el DAG se construye sin ciclos.')
        if spec['memory_task'] and spec['memory_task'] not in {t['id'] for t in memory.load(root)['tasks']}:
            raise KitError('Tarea de PROJECT MEMORY inexistente.')
        state['jobs'].append({'id': spec['id'], 'spec': spec, 'status': 'queued', 'attempts': [],
            'created_at': now(), 'reason': None, 'provider': None, 'model': None})
        store.audit(root, 'job.add', {'id': spec['id'], 'spec_sha256': digest(spec)})
    return {'id': spec['id'], 'execution_resource': execution_resource(root, spec), 'already_added': False}


def overlap(a, b):
    a, b = a.casefold().rstrip('/'), b.casefold().rstrip('/')
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


def conflicts(a, b):
    return any(overlap(x, y) for x in a['writes'] for y in b['writes'] + b['reads']) or any(overlap(x, y) for x in a['reads'] for y in b['writes'])


def clean_environment(workspace):
    temp = workspace / '_runtime_tmp'
    temp.mkdir(exist_ok=True)
    env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR', 'COMSPEC') if key in os.environ}
    env.update({'PATH': str(Path(sys.executable).parent), 'TMP': str(temp), 'TEMP': str(temp),
        'PYTHONIOENCODING': 'utf-8', 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    return env


def invoke(workspace, tool, args, timeout, spec, tools):
    if tool not in tools:
        raise KitError('No existe adaptador ejecutable para la herramienta.')
    argv = [tools[tool]['executable'], *args]
    container_name = None
    if spec['isolation'] == 'container':
        docker = shutil.which('docker')
        if not docker:
            raise KitError('Docker no disponible; no se permite fallback nativo para código no revisado.')
        container_name = 'uasek-' + uuid.uuid4().hex
        argv = [docker, 'run', '--rm', '--name', container_name, '--network', 'none', '--read-only', '--cap-drop=ALL',
            '--security-opt=no-new-privileges', '--pids-limit', '64', '--cpus', '1', '--memory', '256m',
            '--user', '65534:65534', '--tmpfs', '/tmp:rw,nosuid,size=64m', '--mount',
            'type=bind,src=' + str(workspace) + ',dst=/workspace', '--workdir', '/workspace', spec['image'], tools[tool]['container_command'], *args]
    out, err = workspace / ('_stdout-' + uuid.uuid4().hex), workspace / ('_stderr-' + uuid.uuid4().hex)
    started = time.monotonic()
    with out.open('wb') as stdout, err.open('wb') as stderr:
        process = subprocess.Popen(argv, cwd=workspace, env=clean_environment(workspace), stdout=stdout, stderr=stderr,
            start_new_session=os.name != 'nt', creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=10)
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if container_name:
                subprocess.run([docker, 'rm', '--force', container_name], capture_output=True, timeout=15)
            process.wait(timeout=10)
    def bounded(path):
        with path.open('rb') as stream:
            text = redact(stream.read(64000).decode('utf-8', errors='replace'))
        atomic_write(path, text)
        return text
    return {'tool': tool, 'args': args, 'returncode': 124 if timed_out else process.returncode,
        'stdout': bounded(out), 'stderr': bounded(err), 'timed_out': timed_out,
        'duration_seconds': round(time.monotonic()-started, 6)}


def diagnose(result):
    if result.get('error'):
        return {'cause': 'executor-error', 'proposal': 'Revisar contrato, permisos, aislamiento y entradas declaradas.'}
    if any(check.get('timed_out') for check in result.get('commands', [])):
        return {'cause': 'timeout', 'proposal': 'Medir bloqueo/latencia; revisar entradas antes de aumentar el límite.'}
    if any(check.get('returncode') for check in result.get('commands', [])):
        return {'cause': 'command-failed', 'proposal': 'Reproducir en workspace aislado, revisar stderr y corrección declarada; ejecutar regresión.'}
    if not result.get('quality', {}).get('passed'):
        return {'cause': 'quality-gate-failed', 'proposal': 'Corregir el gate incumplido y repetir la regresión dentro del límite de intentos.'}
    return {'cause': None, 'proposal': None}


def execute(root, job, token, gates, timeout, model):
    spec = job['spec']
    folder = safe_path(root, '.uasek/eip/workspaces/' + token)
    if not folder.is_dir():
        raise KitError('Workspace no reservado por el coordinador.')
    result = {'workspace': str(folder.relative_to(Path(root).resolve())), 'commands': [],
              'base': {}, 'outputs': {}, 'provider': 'local-tool', 'model': (spec['command'] or {}).get('tool', 'pending-model-selection'), 'quality': {'passed': False, 'checks': []}}
    try:
        for relative in sorted(set(spec['reads'] + spec['writes'])):
            path = safe_path(root, relative)
            expected = job['reserved_base'][relative]
            result['base'][relative] = expected
            if path.exists():
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != expected:
                    raise KitError('La entrada/base cambió después de autorizar y antes de copiarla: ' + relative)
                if len(raw) > 5_000_000 or redact(raw.decode('utf-8')) != raw.decode('utf-8'):
                    raise KitError('Entrada grande o con posible secreto; no se copiará al ejecutor.')
                target = safe_path(folder, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            elif relative in spec['reads'] or expected is not None:
                raise KitError('Entrada declarada inexistente: ' + relative)
        deadline = time.monotonic() + timeout
        tools = adapters.catalog(root)
        def runner(tool, args):
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                return {'tool': tool, 'args': args, 'returncode': 124, 'timed_out': True, 'stdout': '', 'stderr': 'Presupuesto temporal agotado.'}
            outcome = invoke(folder, tool, args, remaining, spec, tools)
            result['commands'].append(outcome)
            return outcome
        if len(job['attempts']) > 1 and spec['repair']:
            if runner(spec['repair']['tool'], spec['repair']['args'])['returncode']:
                raise KitError('Corrección declarada falló; no se ejecutará el comando principal.')
        if model:
            if model['adapter'] != 'ollama' or model['privacy'] != 'local' or spec['isolation'] != 'native':
                raise KitError('Solo generación Ollama local nativa está implementada; el adaptador manual no se ejecuta.')
            prompt = safe_path(folder, spec['prompt_file']).read_text(encoding='utf-8')
            if len(prompt.encode('utf-8')) > 200000:
                raise KitError('Prompt supera 200 KB.')
            response = http_json('http://127.0.0.1:11434/api/generate', {'model': model['model'], 'prompt': prompt,
                'stream': False, 'options': {'num_predict': 1024}}, timeout=min(60, max(1, int(deadline-time.monotonic()))))
            if not isinstance(response.get('response'), str):
                raise KitError('Respuesta del modelo inválida.')
            target = safe_path(folder, spec['writes'][0])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(redact(response['response']), encoding='utf-8')
            result.update(provider=model['provider'], model=model['model'],
                measured_tokens={k: response.get(k) for k in ('prompt_eval_count', 'eval_count')},
                estimated_cost_units=model['estimated_cost_units'])
        else:
            outcome = runner(spec['command']['tool'], spec['command']['args'])
            if outcome['returncode']:
                result['diagnosis'] = diagnose(result)
                return result
        combined = gates + spec['gates']
        # Prefix task-local IDs to avoid collisions with project gates.
        combined = [dict(g, id=('task:' if i >= len(gates) else 'project:') + g['id']) for i, g in enumerate(combined)]
        result['quality'] = quality.evaluate(folder, spec['writes'], combined, runner)
        if result['quality']['passed']:
            for relative in spec['writes']:
                path = safe_path(folder, relative)
                if not path.is_file() or path.is_symlink() or path.stat().st_size > 5_000_000:
                    raise KitError('Salida declarada inválida o demasiado grande.')
                result['outputs'][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        result['gates_sha256'] = digest(gates)
    except Exception as exc:
        result['error'] = redact(type(exc).__name__ + ': ' + str(exc))
    result['diagnosis'] = diagnose(result)
    return result


def review_resource(root, job):
    return job['id'] + ':' + digest({'spec': job['spec'], 'outputs': job.get('outputs', {}),
        'current': {relative: file_hash(root, relative) for relative in job.get('base', {})},
        'quality': job.get('quality'), 'workspace': job.get('workspace')})


def run_resource(root,max_workers,max_seconds,max_units):
    return 'run:' + digest({'jobs':[execution_resource(root,j['spec']) for j in store.load(root)['jobs'] if j['status'] not in {'done','discarded'}],
        'max_workers':max_workers,'max_seconds':max_seconds,'max_units':max_units})


def integrate(root, ident, approval=None, resolve=False):
    memory_task = None
    with store.transaction(root) as state:
        job = next((j for j in state['jobs'] if j['id'] == ident), None)
        if not job or job['status'] not in {'review', 'conflict'} or not job.get('quality', {}).get('passed'):
            raise KitError('Trabajo sin entregables válidos pendientes de revisión.')
        resource = review_resource(root, job)
        changed = [p for p, expected in job['base'].items() if file_hash(root, p) != expected]
        if changed and (not resolve or any(p in job['spec']['reads'] for p in changed)):
            job.update(status='conflict', reason='Archivos base cambiaron: ' + ', '.join(changed))
            store.audit(root, 'merge.conflict', {'id': ident, 'paths': changed})
            return {'id': ident, 'status': 'conflict', 'review_resource': resource,
                    'next': 'Revisar y reintentar si cambiaron entradas; aceptar una salida conflictiva requiere aprobación específica.'}
        governance.authorize(root, 'conflict.resolve' if resolve else 'integrate', resource, approval)
        if digest(quality.project_gates(root)) != job['gates_sha256']:
            raise KitError('Los quality gates cambiaron; ejecutar regresión con el contrato nuevo.')
        workspace = safe_path(root, job['workspace'])
        for relative, checksum in job['outputs'].items():
            resource_path(root, relative)
            path = safe_path(workspace, relative)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                raise KitError('Entregable alterado después de validarlo.')
        point = checkpoints.create(root, 'Antes de integrar ' + ident, job['spec']['acceptance'], locked=True)
        journal = {'id': ident, 'checkpoint': point['id'], 'outputs': job['outputs'], 'applied': [], 'complete': False}
        path = safe_path(root, '.uasek/eip/integrations/' + ident + '.json')
        write_json(path, journal)
        # Persist the phase before touching code, so a killed coordinator is diagnosable.
        job.update(status='integrating', checkpoint=point['id'])
        store.save(root, state)
        for relative in job['outputs']:
            text = safe_path(workspace, relative).read_bytes().decode('utf-8')
            atomic_write(safe_path(root, relative), text)
            journal['applied'].append(relative)
            write_json(path, journal)
        journal['complete'] = True
        write_json(path, journal)
        job.update(status='done', integrated_at=now(), reason=None)
        memory_task = job['spec']['memory_task']
        evidence = job['spec']['writes']
        store.audit(root, 'merge.done', {'id': ident, 'files': job['outputs'], 'checkpoint': point['id']})
    if memory_task:
        bound = [j for j in store.load(root)['jobs'] if j['spec']['memory_task'] == memory_task]
        if all(j['status'] == 'done' for j in bound):
            paths = sorted({p for j in bound for p in j['spec']['writes']})
            memory.update_task(root, memory_task, 'done', paths)
    return {'id': ident, 'status': 'done', 'files': evidence, 'checkpoint': point['id']}


def run(root, max_workers=2, max_seconds=120, max_units=100, approvals=None):
    root = Path(root).resolve()
    settings = governance.policy(root)
    approvals = approvals or {}
    if type(max_workers) is not int or not 1 <= max_workers <= settings['max_workers'] or type(max_seconds) not in (int, float) or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise KitError('Presupuesto de concurrencia/tiempo inválido.')
    if type(max_units) not in (int, float) or not math.isfinite(max_units) or not 0 <= max_units <= settings['max_units_per_run']:
        raise KitError('Presupuesto de unidades inválido.')
    ident = 'RUN-' + uuid.uuid4().hex[:16]
    deadline = time.monotonic() + max_seconds
    with store.transaction(root) as state:
        governance.authorize(root, 'plan.write', run_resource(root,max_workers,max_seconds,max_units), approvals.get('plan.write'))
        state['runs'].append({'id': ident, 'status': 'running', 'at': now(), 'attempts_reserved': 0,
            'units_reserved': 0, 'max_units': max_units, 'max_workers': max_workers, 'max_seconds': max_seconds})
        store.audit(root, 'run.start', {'id': ident})
    peak = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        while time.monotonic() < deadline:
            batch = []
            with store.transaction(root) as state:
                record = next(r for r in state['runs'] if r['id'] == ident)
                by_id = {job['id']: job for job in state['jobs']}
                active = [j for j in state['jobs'] if j['status'] in {'running', 'review', 'conflict', 'integrating'}]
                for job in state['jobs']:
                    if job['status'] not in {'queued', 'blocked'}:
                        continue
                    if len(batch) >= max_workers or sum(j['status'] == 'running' for j in active) >= settings['max_workers'] or record['attempts_reserved'] >= settings['max_jobs_per_run']:
                        break
                    spec = normalize_spec(root, job['spec'])
                    dependencies = [by_id[d] for d in spec['depends_on']]
                    reason = None
                    if any(dep['status'] != 'done' for dep in dependencies):
                        reason = 'dependency-not-completed'
                    elif any(conflicts(spec, other['spec']) for other in active if other['id'] != job['id']):
                        reason = 'resource-reserved-by-another-job'
                    elif len(job['attempts']) >= spec['max_attempts']:
                        job.update(status='failed', reason='attempt-budget-exhausted')
                        continue
                    if reason:
                        job.update(status='blocked', reason=reason)
                        continue
                    model = None
                    units = spec['budget_units']
                    try:
                        if spec['model_requirements']:
                            model = routing.select(root, spec['model_requirements'])['selected']
                            units = max(units, model['estimated_cost_units'])
                        if record['units_reserved'] + units > max_units:
                            job.update(status='blocked', reason='execution-budget-exhausted')
                            continue
                        base = {path:file_hash(root,path) for path in sorted(set(spec['reads'] + spec['writes']))}
                        gates = deepcopy(quality.project_gates(root))
                        resource = execution_resource(root, spec, base, gates)
                        governance.authorize(root, 'execute', resource, approvals.get('execute:' + job['id']))
                        tools = adapters.catalog(root)
                        commands = [spec['command'], spec['repair']] + [g for g in spec['gates'] + quality.project_gates(root) if g['kind'] == 'command']
                        additional = {permission for command in commands if command for permission in tools[command['tool']]['permissions']} - {'execute'}
                        used_extensions = [m for m in state['extensions'] if m['id']==spec['agent'] or m['id'] in spec['skills']]
                        additional |= {permission for manifest in used_extensions for permission in manifest['permissions']} - {'execute'}
                        for action in sorted(additional):
                            governance.authorize(root, action, resource, approvals.get(action + ':' + job['id']))
                        if model:
                            governance.authorize(root, 'model.invoke', resource, approvals.get('model.invoke:' + job['id']))
                        if spec['environment'] in {'staging', 'production'}:
                            action = 'deploy.' + spec['environment']
                            governance.authorize(root, action, resource, approvals.get(action + ':' + job['id']))
                    except KitError as exc:
                        job.update(status='blocked', reason=str(exc))
                        continue
                    timeout = min(spec['timeout_seconds'], max(0.01, deadline-time.monotonic()))
                    token = uuid.uuid4().hex
                    # Reserve all filesystem parents before concurrent workers start.
                    # Besides ownership, this avoids non-existent-path resolution races on Windows.
                    safe_path(root, '.uasek/eip/workspaces/' + token).mkdir(parents=True, exist_ok=False)
                    job.update(status='running', reason=None, attempt_token=token, run_id=ident, reserved_base=base,
                        lease_expires_at=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=timeout+30)).isoformat())
                    job['attempts'].append({'token': token, 'started_at': now(), 'units_reserved': units})
                    record['attempts_reserved'] += 1
                    record['units_reserved'] += units
                    active.append(job)
                    batch.append((deepcopy(job), token, gates, timeout, model))
                    store.audit(root, 'job.reserve', {'id': job['id'], 'token': token, 'units': units})
            if not batch:
                break
            peak = max(peak, len(batch))
            futures = {pool.submit(execute, root, *args): args for args in batch}
            for future in as_completed(futures):
                source_job, token, _, _, _ = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {'error': redact(type(exc).__name__ + ': ' + str(exc)), 'quality': {'passed': False}, 'diagnosis': {'cause': 'worker-failed', 'proposal': 'Revisar workspace y contrato antes de reintentar.'}}
                auto_merge = False
                with store.transaction(root) as state:
                    job = next(j for j in state['jobs'] if j['id'] == source_job['id'])
                    if job.get('attempt_token') != token or job['status'] != 'running':
                        store.audit(root, 'job.late-result-discarded', {'id': job['id'], 'token': token})
                        continue
                    job['attempts'][-1].update(finished_at=now(), result=redact_data(result))
                    job.update({key: value for key, value in result.items() if key in {'workspace', 'base', 'outputs', 'quality', 'provider', 'model', 'gates_sha256', 'diagnosis', 'measured_tokens', 'estimated_cost_units'}})
                    if result.get('quality', {}).get('passed') and not result.get('error'):
                        job.update(status='review', reason=None)
                        auto_merge = 'integrate' in governance.MATRIX[governance.policy(root)['level']]
                    else:
                        job.update(status='queued' if len(job['attempts']) < job['spec']['max_attempts'] else 'failed',
                            reason=result.get('error') or result.get('diagnosis', {}).get('cause') or 'quality-failed')
                    store.audit(root, 'job.result', {'id': job['id'], 'status': job['status'], 'token': token})
                if auto_merge:
                    try:
                        integrate(root, source_job['id'])
                    except KitError as exc:
                        with store.transaction(root) as state:
                            job = next(j for j in state['jobs'] if j['id'] == source_job['id'])
                            job['reason'] = str(exc)
                            store.audit(root, 'merge.blocked', {'id': job['id'], 'reason': str(exc)})
    with store.transaction(root) as state:
        record = next(r for r in state['runs'] if r['id'] == ident)
        record.update(status='finished', finished_at=now(), peak_parallel_workers=peak)
        record['jobs'] = {job['id']: job['status'] for job in state['jobs']}
        store.audit(root, 'run.finish', record)
        summary = deepcopy(record)
    return summary


def recover(root):
    recovered, needs_review = [], []
    with store.transaction(root) as state:
        governance.authorize(root, 'plan.write', 'recover-expired-leases')
        current = dt.datetime.now(dt.timezone.utc)
        for job in state['jobs']:
            if job['status'] == 'integrating':
                needs_review.append({'id': job['id'], 'checkpoint': job.get('checkpoint'),
                    'proposal': 'Integración interrumpida; revisar journal y recuperar checkpoint en carpeta nueva antes de integrar.'})
            elif job['status'] == 'running' and dt.datetime.fromisoformat(job['lease_expires_at']) <= current:
                job.update(status='queued' if len(job['attempts']) < job['spec']['max_attempts'] else 'failed',
                    reason='expired-lease-interrupted', attempt_token=None)
                job['attempts'][-1].update(interrupted=True, finished_at=now())
                recovered.append(job['id'])
        for record in state['runs']:
            if record['status'] == 'running' and not any(j.get('run_id') == record['id'] and j['status'] == 'running' for j in state['jobs']):
                record.update(status='interrupted', finished_at=now())
        store.audit(root, 'recovery.leases', {'recovered': recovered, 'needs_review': needs_review})
    return {'recovered': recovered, 'needs_review': needs_review, 'limits': 'No mata procesos ajenos ni sobrescribe código; resultados de leases antiguos se descartan.'}


def resolve(root, ident, decision, approval):
    if decision == 'accept':
        return integrate(root, ident, approval, resolve=True)
    if decision not in {'retry', 'discard'}:
        raise KitError('Resolución debe ser accept, retry o discard.')
    with store.transaction(root) as state:
        job = next((j for j in state['jobs'] if j['id'] == ident), None)
        if not job or job['status'] not in {'conflict', 'review', 'failed', 'blocked'}:
            raise KitError('Trabajo sin conflicto o revisión pendiente.')
        resource = review_resource(root, job)
        governance.authorize(root, 'conflict.resolve', resource, approval)
        if decision == 'retry' and len(job['attempts']) >= job['spec']['max_attempts']:
            raise KitError('Intentos agotados; crear nuevo contrato revisado.')
        job.update(status='queued' if decision == 'retry' else 'discarded', reason='reviewed-' + decision)
        store.audit(root, 'conflict.resolve', {'id': ident, 'decision': decision})
    return {'id': ident, 'status': job['status']}
