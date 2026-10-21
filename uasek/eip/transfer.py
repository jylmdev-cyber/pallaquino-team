"""Portable brain sidecar; imported automation/security remain review proposals."""
from copy import deepcopy
import json
from pathlib import Path

from . import governance, store
from ..common import KitError, now, read_json, redact_data, safe_path, write_json
from ..context_format import digest

PATH = 'project-memory/PLATFORM_CONTEXT.json'


def export(root, dry_run=False):
    state = store.load(root)
    facts = redact_data({'records': state['records'], 'traces': state['traces'], 'relations': state['relations'],
        'job_proposals': [{'spec': job['spec'], 'historical_status': job['status'], 'provider': job.get('provider'),
                           'model': job.get('model'), 'attempt_count': len(job['attempts'])} for job in state['jobs']],
        'extension_proposals': state['extensions']})
    payload = {'format': 'uasek.platform-context', 'format_version': 1, 'source_project_id': state['project_id'],
        'exported_at': now(), 'facts': facts, 'facts_sha256': digest(facts)}
    if len(json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')) > 2_000_000:
        raise KitError('Contexto de plataforma supera 2 MB.')
    if not dry_run:
        write_json(safe_path(root, PATH), payload)
    return {'path': str(safe_path(root, PATH)), 'format_version': 1, 'facts_sha256': payload['facts_sha256'], 'dry_run': dry_run}


def import_context(root, filename, approval=None, dry_run=False):
    if Path(filename).stat().st_size > 2_000_000:
        raise KitError('Contexto de plataforma demasiado grande.')
    payload = read_json(filename)
    required = {'format', 'format_version', 'source_project_id', 'exported_at', 'facts', 'facts_sha256'}
    if not isinstance(payload, dict) or set(payload) != required or payload['format'] != 'uasek.platform-context' or type(payload['format_version']) is not int or payload['format_version'] != 1:
        raise KitError('Formato de plataforma incompatible.')
    facts = payload['facts']
    if not isinstance(facts, dict) or set(facts) != {'records', 'traces', 'relations', 'job_proposals', 'extension_proposals'} or digest(facts) != payload['facts_sha256'] or any(not isinstance(v, list) for v in facts.values()):
        raise KitError('Integridad o estructura de plataforma inválida.')
    if any(not isinstance(item, dict) or not {'id','kind','text','sources','status','created_at'} <= set(item) or not isinstance(item['text'], str) or not isinstance(item['sources'], list) for item in facts['records']):
        raise KitError('Registro de memoria importado inválido.')
    for item in facts['records']:
        for source in item['sources']:
            if not isinstance(source, dict) or not isinstance(source.get('path'), str):
                raise KitError('Fuente de memoria importada inválida.')
            safe_path(root, source['path'])
    for item in facts['traces']:
        if not isinstance(item, dict) or not {'id','kind','path','title','sha256','at'} <= set(item):
            raise KitError('Nodo importado inválido.')
        safe_path(root, item['path'])
    node_ids = {n['id'] for n in facts['traces']}
    if len(node_ids) != len(facts['traces']) or any(not isinstance(edge, dict) or edge.get('source') not in node_ids or edge.get('target') not in node_ids or not isinstance(edge.get('relation'), str) for edge in facts['relations']):
        raise KitError('Relaciones importadas inválidas.')
    resource = payload['facts_sha256']
    if dry_run:
        return {'resource': resource, 'records': len(facts['records']), 'jobs_will_execute': False, 'dry_run': True}
    with store.transaction(root) as state:
        governance.authorize(root, 'memory.write', resource, approval)
        # Preserve identifiers only when they do not conflict; never silently replace local facts.
        for key in ('records', 'traces'):
            by_id = {item['id']: item for item in state[key]}
            for item in facts[key]:
                if item['id'] in by_id and by_id[item['id']] != item:
                    raise KitError('Conflicto de memoria importada; requiere reconciliación explícita.')
                if item['id'] not in by_id:
                    state[key].append(deepcopy(item))
        for edge in facts['relations']:
            if edge not in state['relations']:
                state['relations'].append(edge)
        state.setdefault('imports', [])
        if not any(item['facts_sha256'] == resource for item in state['imports']):
            state['imports'].append({'source_project_id': payload['source_project_id'], 'facts_sha256': resource,
                'at': now(), 'job_proposals': facts['job_proposals'], 'extension_proposals': facts['extension_proposals'],
                'review_required': True})
        store.audit(root, 'brain.import', {'source_project_id': payload['source_project_id'], 'facts_sha256': resource})
    return {'records': len(facts['records']), 'active_jobs_added': 0, 'permissions_imported': False, 'dry_run': False}
