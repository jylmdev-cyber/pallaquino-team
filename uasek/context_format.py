"""Versioned universal context: project facts are separate from adapter instructions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from . import memory
from .common import (KitError, now, read_json, redact_data, safe_path,
                     state_lock, write_json)

FORMAT = 'uasek.project-context'
VERSION = 1
CONTEXT_PATH = 'project-memory/PROJECT_CONTEXT.json'


def digest(value):
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def envelope(state):
    """Provider identity and adapter instructions deliberately stay outside state."""
    state = deepcopy(state)
    state.pop('provider', None)
    facts = redact_data(state)
    return {'format': FORMAT, 'format_version': VERSION, 'exported_at': now(),
            'state': facts, 'state_sha256': digest(facts)}


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != {'format', 'format_version', 'exported_at', 'state', 'state_sha256'}:
        raise KitError('Sobre de contexto inválido.')
    if payload['format'] != FORMAT or type(payload['format_version']) is not int or payload['format_version'] != VERSION:
        raise KitError('Versión de contexto no soportada; requiere migración explícita.')
    if not isinstance(payload['state'], dict) or 'provider' in payload['state']:
        raise KitError('El contexto universal no admite configuración de proveedor.')
    if digest(payload['state']) != payload['state_sha256']:
        raise KitError('Checksum del contexto no coincide.')
    state = deepcopy(payload['state'])
    state['provider'] = {'name': 'manual', 'mode': 'assistant'}
    memory.validate_state(state)
    return state


def export(root, dry_run=False):
    payload = envelope(memory.load(root))
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    if len(serialized.encode('utf-8')) > 2_000_000:
        raise KitError('Contexto supera 2 MB; resumir antes de exportar.')
    validate(payload)
    target = safe_path(root, CONTEXT_PATH)
    if not dry_run:
        write_json(target, payload)
    return {'path': str(target), 'format': FORMAT, 'format_version': VERSION,
            'state_sha256': payload['state_sha256'], 'dry_run': dry_run}


def import_context(root, filename, replace=False, dry_run=False):
    filename = Path(filename)
    if filename.stat().st_size > 2_000_000:
        raise KitError('Contexto supera 2 MB.')
    incoming = validate(read_json(filename))
    current = memory.load(root)
    meaningful = ('tasks', 'decisions', 'architecture', 'stack', 'known_issues', 'technical_debt',
                  'audits', 'next_actions', 'validated_checkpoint', 'files_involved')
    project_facts = ('description', 'objectives', 'functional_requirements', 'non_functional_requirements')
    nonempty = any(current[key] for key in meaningful) or any(current['project'][key] for key in project_facts)
    if nonempty and not replace:
        raise KitError('Ya hay contexto. Use --replace-memory para sustituirlo con checkpoint previo.')
    incoming['provider'] = current['provider']
    missing = []
    for task in incoming['tasks']:
        for relative in task['evidence']:
            path = safe_path(root, relative)
            if not path.is_file():
                missing.append({'task': task['id'], 'path': relative})
    incoming['history'].append(now() + ' contexto universal importado; evidencias requieren revisión local.')
    preview = {'imported_project': incoming['project']['name'], 'tasks': len(incoming['tasks']),
               'unverified_evidence': missing, 'local_provider_preserved': current['provider'], 'dry_run': dry_run}
    if dry_run:
        return preview
    with state_lock(root):
        if memory.load(root) != current:
            raise KitError('La memoria cambió durante la importación; repetir.')
        if nonempty:
            from .checkpoints import create
            preview['previous_checkpoint'] = create(root, 'Antes de importar contexto',
                'Conservar memoria anterior para recuperación', locked=True)['id']
        memory.save(root, incoming)
    return preview
