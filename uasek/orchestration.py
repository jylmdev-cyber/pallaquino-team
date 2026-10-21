"""Explainable role selection and idempotent, checkpointed task planning."""
from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
import re
import unicodedata

from . import checkpoints, memory
from .common import (KitError, now, read_json, redact, RESOURCE_ROOT,
                     safe_path, state_lock, write_json)
from .context_format import digest


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))


def matches(text, phrases):
    return [phrase for phrase in phrases if re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text)]


def plan(root, request, kind='auto', max_roles=4, paths=()):
    root = Path(root).resolve()
    if not request.strip() or len(request) > 20000:
        raise KitError('Solicitud requerida, máximo 20000 caracteres.')
    if type(max_roles) is not int or not 1 <= max_roles <= 8:
        raise KitError('--max-roles debe estar entre 1 y 8.')
    rules = read_json(RESOURCE_ROOT / 'configs/orchestration.json')
    if kind not in ['auto', *rules['kinds']]:
        raise KitError('Tipo de trabajo desconocido.')
    memory.load(root)
    normalized_paths = [safe_path(root, p).relative_to(root).as_posix() for p in paths]
    text = normalize(request)
    if kind == 'auto':
        kind = next((name for name, words in rules['classifiers'] if matches(text, words)), 'feature')
    selected = {}

    def add(role, score, reason):
        item = selected.setdefault(role, {'role': role, 'score': score, 'reasons': []})
        item['score'] = max(score, item['score'])
        item['reasons'].append(reason)

    for role, score in rules['kinds'][kind]:
        add(role, score, 'Trabajo de tipo ' + kind)
    if kind not in ('docs', 'audit'):
        for item in rules['signals']:
            found = matches(text, item['terms'])
            if found:
                add(item['role'], item['score'], 'Señales: ' + ', '.join(found))
        for path in normalized_paths:
            for item in rules['path_signals']:
                if any(path.lower().endswith(ext) for ext in item['suffixes']):
                    add(item['role'], item['score'], 'Archivo en alcance: ' + path)
    if not selected:
        add('tech-lead', 100, 'Requiere aclarar alcance antes de implementar.')
    ranked = sorted(selected.values(), key=lambda item: (-item['score'], item['role']))
    chosen, deferred = ranked[:max_roles], ranked[max_roles:]
    order = {role: index for index, role in enumerate(rules['execution_order'])}
    chosen.sort(key=lambda item: order[item['role']])
    steps = []
    contracts = memory.agents()
    for index, item in enumerate(chosen, 1):
        contract = contracts[item['role']]
        steps.append({'step': index, 'role': item['role'], 'reasons': item['reasons'],
                      'title': contract['role'] + ': ' + redact(request[:160]),
                      'acceptance': contract['acceptance_criteria'][0] + ' Resultado esperado: ' + redact(request),
                      'depends_on_steps': [index - 1] if index > 1 else [],
                      'files_in_scope': normalized_paths,
                      'authorization_required': item['role'] == 'git-auditor'})
    result = {'format': 'uasek.orchestration-plan', 'format_version': 1,
              'request': redact(request), 'kind': kind, 'max_roles': max_roles,
              'steps': steps, 'deferred_roles': deferred,
              'execution_policy': {'max_parallel': 1, 'model_calls': 0,
                  'conflicts': 'Secuencial por defecto; no hay escritores simultáneos ni modelos invocados por el planificador.',
                  'review': 'Revisar roles diferidos y criterios antes de implementar. Ningún plan autoriza auditorías, producción o efectos externos.'}}
    result['id'] = 'PLAN-' + digest(result)[:16]
    return result


def apply(root, proposal, dry_run=False):
    """Only materialize our validated deterministic plans, never execute their text."""
    with (nullcontext() if dry_run else state_lock(root)):
        # Rebuild from bounded input so callers cannot inject arbitrary steps/contracts.
        rebuilt = plan(root, proposal['request'], proposal['kind'], proposal['max_roles'],
                       proposal['steps'][0]['files_in_scope'])
        if proposal != rebuilt:
            raise KitError('Plan alterado; regenerar con el planificador.')
        essential = {item['role'] for item in proposal['deferred_roles']} & {'security-engineer', 'qa-engineer'}
        if essential:
            raise KitError('Presupuesto de roles insuficiente para controles requeridos: ' + ', '.join(sorted(essential)) + '. Aumente --max-roles.')
        state = deepcopy(memory.load(root))
        path = safe_path(root, 'ai/plans/' + proposal['id'] + '.json')
        if path.exists():
            record = read_json(path)
            expected = record.get('task_ids', [])
            by_id = {t['id']: t for t in state['tasks']}
            if record.get('plan') != proposal or not expected or any(t not in by_id for t in expected):
                raise KitError('Registro de plan inconsistente; revisar sin duplicar tareas.')
            if len(expected) != len(proposal['steps']):
                raise KitError('Cantidad de tareas del plan inconsistente.')
            for index, step in enumerate(proposal['steps']):
                task = by_id[expected[index]]
                if any(task[key] != value for key, value in {
                    'agent': step['role'], 'title': step['title'], 'acceptance': step['acceptance'],
                    'depends_on': expected[index-1:index] if index else []}.items()):
                    raise KitError('Tareas del plan cambiaron; revisar antes de reusar el recibo.')
            return {'plan_id': proposal['id'], 'task_ids': expected, 'already_applied': True, 'dry_run': dry_run}
        number = max([int(t['id'][1:]) for t in state['tasks']] or [0])
        task_ids = []
        for step in proposal['steps']:
            number += 1
            ident = f'T{number:04}'
            task_ids.append(ident)
            state['tasks'].append({'id': ident, 'title': step['title'], 'agent': step['role'],
                'acceptance': step['acceptance'], 'depends_on': task_ids[-2:-1], 'status': 'todo',
                'evidence': [], 'created_at': now(), 'updated_at': now()})
        memory.validate_state(state)
        if dry_run:
            return {'plan_id': proposal['id'], 'task_ids': task_ids, 'dry_run': True}
        point = checkpoints.create(root, 'Antes de ' + proposal['id'], proposal['request'], locked=True)
        state['history'].append(now() + ' plan aplicado: ' + proposal['id'] + '; checkpoint ' + point['id'])
        # Write receipt first: if memory save fails, a retry fails closed rather than duplicating work.
        write_json(path, {'plan': proposal, 'task_ids': task_ids, 'checkpoint': point['id']})
        memory.save(root, state)
        return {'plan_id': proposal['id'], 'task_ids': task_ids, 'checkpoint': point['id'],
                'already_applied': False, 'dry_run': False}
