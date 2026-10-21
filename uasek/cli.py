"""Single argparse surface reused by every tools/*.py entry point."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import logging
from pathlib import Path
import subprocess
import sys
import urllib.error

from .common import (KIT_ROOT, RESOURCE_ROOT, KitError, atomic_write, event, now, read_json,
                     redact, redact_data, safe_path, state_lock)
from . import memory, operations, providers, context_format, checkpoints, orchestration


def parser():
    p = argparse.ArgumentParser(description='UASEK — herramientas operativas de ingeniería asistida por IA.')
    p.add_argument('--root', default='.', help='Proyecto objetivo (predeterminado: carpeta actual). Colocar antes del subcomando.')
    p.add_argument('--output', help='Guardar resultado JSON redactado; no sobrescribe archivos existentes.')
    p.add_argument('--verbose', action='store_true')
    p.add_argument('--platform-approval', help='Aprobación acotada de EIP para comandos anteriores cuando el nivel la exija.')
    p.add_argument('--policy-preview', action='store_true', help='Mostrar permiso y recurso del comando sin ejecutarlo.')
    sub = p.add_subparsers(dest='command')

    def command(name, help_text, dry=False):
        child = sub.add_parser(name, help=help_text, description=help_text)
        if dry:
            child.add_argument('--dry-run', action='store_true', help='Validar y mostrar sin escribir ni ejecutar.')
        return child

    init = command('init', 'Crear memoria y estructura de proyecto en una carpeta nueva.', True)
    init.add_argument('--destination', required=True)
    init.add_argument('--name', required=True)
    init.add_argument('--description', default='')
    init.add_argument('--template', help='ID del catálogo; documentación de referencia, no aplicación completa.')
    init.add_argument('--existing', action='store_true', help='Incorporar solo memoria a carpeta existente; rechaza si ya tiene project-memory.')
    command('analyze', 'Inventariar archivos y manifiestos sin ejecutar código.')
    au = command('audit', 'Auditoría Git de solo lectura autorizada por el usuario.')
    au.add_argument('--authorize', action='store_true', help='Usar solo después de obtener autorización del propietario.')
    au.add_argument('--full', action='store_true')
    command('status', 'Estado, dependencias y tareas listas.')
    command('doctor', 'Verificar Python, Git y existencia de memoria.')
    command('security', 'Escaneo estático heurístico; salida sin valores secretos.')
    dep = command('dependency', 'Inventario de versiones exactas; consulta OSV opcional.')
    dep.add_argument('--online', action='store_true')
    stack = command('stack', 'Consultar metadatos de versión en registros oficiales.')
    stack.add_argument('--ecosystem', choices=['pypi', 'npm'], default='pypi')
    stack.add_argument('--package', required=True)
    stack.add_argument('--online', action='store_true')
    command('docs', 'Actualizar documentos derivados conservando documentos manuales.', True)
    test = command('test', 'Ejecutar unittest del proyecto (ejecuta código local).', True)
    test.add_argument('--timeout', type=int, default=120)
    back = command('backup', 'Respaldar código de texto con manifiesto SHA-256; excluye datos y secretos.', True)
    back.add_argument('--destination', required=True)
    rel = command('release', 'Preparar reporte local; no publica ni despliega.', True)
    rel.add_argument('--version', required=True)
    command('handoff', 'Exportar memoria seleccionada y redactada para otro asistente.', True)

    context = command('context', 'Consultar, actualizar o exportar PROJECT MEMORY.', True)
    context.add_argument('action', choices=['show', 'update', 'export', 'import'])
    context.add_argument('--file', help='JSON con campos de memoria a actualizar. No admite tareas ni historial.')
    context.add_argument('--replace-memory', action='store_true', help='Importar sobre memoria existente, guardando checkpoint previo.')
    checkpoint = command('checkpoint', 'Capturar y verificar código/memoria/pruebas o recuperar en carpeta nueva.', True)
    checkpoint.add_argument('action', choices=['create', 'list', 'show', 'verify', 'restore'])
    checkpoint.add_argument('--id')
    checkpoint.add_argument('--label')
    checkpoint.add_argument('--expected', help='Resultado esperado del cambio que se realizará después.')
    checkpoint.add_argument('--destination', help='Para restore: carpeta nueva fuera del proyecto.')
    orchestrate = command('orchestrate', 'Seleccionar roles con reglas locales y aplicar un plan con checkpoint previo.', True)
    orchestrate.add_argument('--request', required=True)
    orchestrate.add_argument('--kind', choices=['auto', 'new', 'feature', 'fix', 'docs', 'audit', 'migration'], default='auto')
    orchestrate.add_argument('--max-roles', type=int, default=4)
    orchestrate.add_argument('--file', action='append', default=[], help='Archivo en alcance, relativo al proyecto. Repetible.')
    orchestrate.add_argument('--apply', action='store_true', help='Crear tareas del plan una sola vez y checkpoint antes de cambiar memoria.')
    provider = command('provider', 'Listar capacidades, preparar transferencia o invocar Ollama local.', True)
    provider.add_argument('action', choices=['list', 'switch', 'generate'])
    provider.add_argument('--provider', default='manual')
    provider.add_argument('--mode', choices=['assistant', 'api'], default='assistant')
    provider.add_argument('--model')
    provider.add_argument('--prompt-file')
    provider.add_argument('--endpoint', default='http://127.0.0.1:11434')
    task = command('task', 'Administrar tareas, dependencias y evidencia verificable.', True)
    task.add_argument('action', choices=['list', 'add', 'update', 'ready'])
    task.add_argument('--title')
    task.add_argument('--agent', default='tech-lead')
    task.add_argument('--acceptance')
    task.add_argument('--depends-on', action='append', default=[])
    task.add_argument('--id')
    task.add_argument('--status', choices=memory.STATES)
    task.add_argument('--evidence', action='append', default=[])
    agent = command('agent', 'Consultar contratos o generar encargo persistente para una tarea.', True)
    agent.add_argument('action', choices=['list', 'show', 'brief', 'validate'])
    agent.add_argument('--name')
    agent.add_argument('--task')
    agent.add_argument('--result', help='JSON AgentResult; valida estructura y existencia de artefactos, sin cerrar tareas.')
    command('catalog', 'Listar 30 referencias de sistemas por rubro.')
    from .eip.cli import attach
    attach(sub)
    return p


def require(value, name):
    if value is None:
        raise KitError('Falta ' + name)
    return value


def context_update(root, filename, dry_run):
    patch = read_json(require(filename, '--file'))
    allowed = {'project': dict, 'architecture': str, 'stack': list, 'decisions': list,
               'known_issues': list, 'technical_debt': list, 'next_actions': list,
               'validated_checkpoint': (str, type(None)), 'audits': list}
    if not isinstance(patch, dict) or set(patch) - set(allowed):
        raise KitError('Campos permitidos: ' + ', '.join(allowed))
    for key, value in patch.items():
        if not isinstance(value, allowed[key]):
            raise KitError('Tipo inválido para ' + key)
    for key in ('decisions', 'known_issues', 'technical_debt', 'next_actions'):
        if key in patch and any(not isinstance(v, str) for v in patch[key]):
            raise KitError(key + ' requiere una lista de textos.')
    if 'project' in patch:
        project = patch['project']
        if set(project) - {'name', 'description', 'objectives', 'functional_requirements', 'non_functional_requirements'}:
            raise KitError('Campo de proyecto desconocido.')
        for key, value in project.items():
            if not isinstance(value, str if key in ('name', 'description') else list):
                raise KitError('Tipo de proyecto inválido: ' + key)
    serialized = json.dumps(patch, ensure_ascii=False)
    if redact(serialized) != serialized:
        raise KitError('Se detectó un posible secreto; retirarlo antes de guardar memoria.')
    candidate = deepcopy(memory.load(root))
    for key, value in patch.items():
        candidate[key] = {**candidate['project'], **value} if key == 'project' else value
    memory.validate_state(candidate)
    if not dry_run:
        with state_lock(root):
            state = memory.load(root)
            if 'project' in patch:
                patch['project'] = {**state['project'], **patch['project']}
            state.update(patch)
            state['history'].append(now() + ' memoria actualizada: ' + ', '.join(patch))
            memory.save(root, state)
    return {'updated_fields': list(patch), 'dry_run': dry_run}


def dispatch(args, root):
    command = args.command
    dry = getattr(args, 'dry_run', False)
    if command == 'platform':
        from .eip.cli import dispatch as platform_dispatch
        return platform_dispatch(args, root)
    if command == 'init':
        if args.existing and args.template:
            raise KitError('--existing no admite --template; revise la referencia antes de incorporarla.')
        return operations.init_project(args.destination, args.name, args.description, args.template, dry, args.existing)
    if command == 'analyze':
        return operations.analyze(root)
    if command == 'audit':
        return operations.audit(root, args.authorize, args.full)
    if command == 'doctor':
        return operations.doctor(root)
    if command == 'security':
        return operations.scan(root)
    if command == 'dependency':
        return operations.dependencies(root, args.online)
    if command == 'stack':
        return operations.stack_check(args.ecosystem, args.package, args.online)
    if command == 'docs':
        return operations.generate_docs(root, dry)
    if command == 'test':
        if args.timeout <= 0:
            raise KitError('--timeout debe ser positivo.')
        return operations.test_run(root, args.timeout, dry)
    if command == 'backup':
        return operations.backup(root, args.destination, dry)
    if command == 'release':
        return operations.release(root, args.version, dry)
    if command == 'handoff':
        return memory.handoff(root, dry_run=dry)
    if command == 'checkpoint':
        if args.action == 'list':
            return checkpoints.list_checkpoints(root)
        if args.action == 'create':
            return checkpoints.create(root, require(args.label, '--label'), require(args.expected, '--expected'), dry)
        if args.action == 'restore':
            return checkpoints.restore(root, require(args.id, '--id'), require(args.destination, '--destination'), dry)
        record = checkpoints.inspect(root, require(args.id, '--id'))
        return record if args.action == 'show' else {'id': record['id'], 'integrity_verified': True,
                                                     'tests_fresh_when_captured': record['tests_fresh_and_passing']}
    if command == 'orchestrate':
        proposal = orchestration.plan(root, args.request, args.kind, args.max_roles, args.file)
        return {'plan': proposal, 'application': orchestration.apply(root, proposal, dry)} if args.apply else proposal
    if command == 'context':
        if args.action == 'show':
            return memory.load(root)
        if args.action == 'export':
            return memory.handoff(root, dry_run=dry)
        if args.action == 'import':
            return context_format.import_context(root, require(args.file, '--file'), args.replace_memory, dry)
        return context_update(root, args.file, dry)
    if command == 'provider':
        if args.action == 'list':
            return providers.catalog()
        if args.action == 'switch':
            return providers.switch(root, args.provider, args.mode, dry)
        return providers.generate_local(require(args.model, '--model'),
            Path(require(args.prompt_file, '--prompt-file')).read_text(encoding='utf-8-sig'), args.endpoint, dry)
    if command == 'task':
        if args.action == 'add':
            return memory.add_task(root, require(args.title, '--title'), args.agent,
                                   require(args.acceptance, '--acceptance'), args.depends_on, dry)
        if args.action == 'update':
            return memory.update_task(root, require(args.id, '--id'), require(args.status, '--status'), args.evidence, dry)
        state = memory.load(root)
        return memory.ready(state) if args.action == 'ready' else state['tasks']
    if command == 'status':
        state = memory.load(root)
        return {'project': state['project'], 'counts': {s: sum(t['status'] == s for t in state['tasks']) for s in memory.STATES},
                'ready': memory.ready(state), 'provider': state['provider'], 'updated_at': state['updated_at']}
    if command == 'agent':
        contracts = memory.agents()
        if args.action == 'list':
            return {k: v['role'] for k, v in contracts.items()}
        if args.action == 'brief':
            return memory.brief(root, require(args.task, '--task'), dry)
        if args.action == 'validate':
            return memory.validate_result(root, require(args.result, '--result'))
        name = require(args.name, '--name')
        if name not in contracts:
            raise KitError('Agente desconocido.')
        return contracts[name]
    if command == 'catalog':
        return read_json(RESOURCE_ROOT / 'configs/catalog.json')
    raise KitError('Comando no implementado.')


def exit_code(command, result):
    if command == 'platform' and isinstance(result, dict):
        return result.get('exit_code', 0)
    if command == 'test':
        return result.get('returncode', 0)
    if command == 'security' and any(f['severity'] == 'high' for f in result['findings']):
        return 1
    if command == 'dependency':
        if result['errors']:
            return 2
        if any(c['vulnerabilities'] for c in result['checks']):
            return 1
        if result['unresolved'] or (result['checks'] and not result['online']):
            return 3  # Coverage incomplete is distinct from clean.
    return 0


def main(argv=None):
    # Deterministic UTF-8 under redirected Windows terminals as well as Unix.
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8')
    args = parser().parse_args(argv)
    if args.command is None:
        print('👋 Listo para desarrollar. ¿Qué proyecto vamos a trabajar?\n\n'
              '1. Crear un sistema nuevo.\n2. Continuar el desarrollo de un sistema existente.\n'
              '3. Agregar funcionalidades a un sistema.\n4. Corregir errores o mejorar un proyecto.\n'
              '5. Modernizar o migrar un sistema.\n6. Auditar un proyecto.\n'
              '7. Consultar los ejemplos de sistemas disponibles.\n\n'
              'Seleccione la intención con su asistente. Consulte python kit.py --help para comandos.')
        return 0
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format='%(levelname)s: %(message)s')
    root = Path(args.root).resolve()
    try:
        if not root.is_dir():
            raise KitError('--root debe ser una carpeta existente.')
        from .eip.cli import legacy_scope, authorize_legacy
        scope = legacy_scope(args, root)
        if args.policy_preview:
            print(json.dumps(scope or {'permission': 'read', 'resource': None}, ensure_ascii=False, indent=2))
            return 0
        output_path = None
        if args.output:
            output_path = Path(args.output).resolve()
            if output_path.exists():
                raise KitError('--output ya existe; no se sobrescribe.')
        authorize_legacy(root, scope, args.platform_approval)
        result = dispatch(args, root)
        text = json.dumps(redact_data(result), ensure_ascii=False, indent=2)
        if output_path and not getattr(args, 'dry_run', False):
            # Explicit report generation is the only write in read-only commands.
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open('x', encoding='utf-8') as stream:
                stream.write(text + '\n')
        print(text)
        code = exit_code(args.command, result)
        mutations = {'init', 'docs', 'backup', 'release', 'test', 'handoff'}
        is_mutation = args.command in mutations or (
            args.command in {'task', 'provider', 'context', 'agent', 'checkpoint'} and args.action in {'add', 'update', 'switch', 'export', 'import', 'brief', 'create', 'restore'}) or (
            args.command == 'orchestrate' and args.apply)
        if is_mutation and not getattr(args, 'dry_run', False) and args.command != 'init':
            event(root, args.command, code)
        return code
    except (KitError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired,
            urllib.error.URLError) as exc:
        logging.error('%s: %s', type(exc).__name__, redact(str(exc)))
        return 2


if __name__ == '__main__':
    sys.exit(main())
