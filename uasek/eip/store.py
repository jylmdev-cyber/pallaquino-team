"""Open JSON state and tamper-evident audit chain, protected by project locks."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import re
import uuid

from .. import memory
from ..common import KitError, now, read_json, redact_data, safe_path, state_lock, write_json
from ..context_format import digest

DIRECTORY = 'project-memory/platform'


def location(root, name):
    return safe_path(root, DIRECTORY + '/' + name)


def initial_policy():
    return {'schema_version': 1, 'level': 'supervisado', 'max_workers': 4,
            'max_attempts': 3, 'max_timeout_seconds': 60, 'max_jobs_per_run': 20,
            'max_units_per_run': 100, 'native_reviewed_code': True,
            'allowed_tools': ['python'], 'allowed_container_images': [],
            'container_network': 'none'}


def initialize(root):
    memory.load(root)
    with state_lock(root):
        if location(root, 'state.json').exists():
            raise KitError('La plataforma ya está inicializada; se conserva su identidad y política.')
        state = {'schema_version': 1, 'api_version': 1, 'project_id': uuid.uuid4().hex,
                 'created_at': now(), 'jobs': [], 'runs': [], 'records': [], 'traces': [],
                 'relations': [], 'extensions': []}
        write_json(location(root, 'policy.json'), initial_policy())
        write_json(location(root, 'gates.json'), {'schema_version': 1, 'gates': [
            {'id': 'evidence', 'kind': 'files_exist', 'mandatory': True},
            {'id': 'syntax', 'kind': 'python_syntax', 'mandatory': True},
            {'id': 'secrets', 'kind': 'no_secrets', 'mandatory': True}]})
        write_json(location(root, 'models.json'), {'schema_version': 1, 'models': []})
        write_json(location(root, 'state.json'), state)
        audit(root, 'platform.init', {'project_id': state['project_id']})
    return {'project_id': state['project_id'], 'level': 'supervisado', 'api_version': 1}


def load(root):
    state = read_json(location(root, 'state.json'))
    if not isinstance(state, dict) or type(state.get('schema_version')) is not int or type(state.get('api_version')) is not int or state.get('schema_version') != 1 or state.get('api_version') != 1:
        raise KitError('Versión de plataforma incompatible; no se migrará implícitamente.')
    if not isinstance(state.get('project_id'), str) or not re.fullmatch(r'[a-f0-9]{32}', state['project_id']):
        raise KitError('Identidad de proyecto inválida.')
    for key in ('jobs', 'runs', 'records', 'traces', 'relations', 'extensions'):
        if not isinstance(state.get(key), list):
            raise KitError('Estado de plataforma inválido: ' + key)
    by_id = {}
    for job in state['jobs']:
        if not isinstance(job, dict) or not isinstance(job.get('id'), str) or not isinstance(job.get('spec'), dict) or job['spec'].get('id') != job['id'] or not isinstance(job.get('attempts'), list):
            raise KitError('Contrato de trabajo persistido inválido.')
        if job['id'] in by_id or job.get('status') not in {'queued','running','blocked','review','conflict','integrating','done','failed','discarded'}:
            raise KitError('Estado o identidad de trabajo inválidos.')
        if not isinstance(job['spec'].get('depends_on'), list) or any(not isinstance(v,str) for v in job['spec']['depends_on']):
            raise KitError('Dependencias de trabajo inválidas.')
        by_id[job['id']] = set(job['spec']['depends_on'])
    if any(deps - set(by_id) for deps in by_id.values()):
        raise KitError('Dependencia de plataforma inexistente.')
    resolved = set()
    while by_id:
        available = {ident for ident, deps in by_id.items() if deps <= resolved}
        if not available:
            raise KitError('Ciclo de dependencias en plataforma.')
        resolved |= available
        by_id = {ident: deps for ident, deps in by_id.items() if ident not in available}
    for record in state['records']:
        if not isinstance(record, dict) or not {'id','kind','text','sources','status','created_at'} <= set(record) or not isinstance(record['text'],str):
            raise KitError('Registro de cerebro inválido.')
    return state


def save(root, state):
    write_json(location(root, 'state.json'), redact_data(state))


def audit(root, action, data):
    """Caller holds state_lock. Hash chains detect corruption, not malicious rewriting."""
    path = location(root, 'audit.jsonl')
    previous = '0' * 64
    if path.exists():
        lines = path.read_text(encoding='utf-8').splitlines()
        if lines:
            previous = json.loads(lines[-1])['sha256']
    record = {'at': now(), 'action': action, 'data': redact_data(data), 'previous': previous}
    record['sha256'] = digest(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')


def verify_audit(root):
    path = location(root, 'audit.jsonl')
    previous, count = '0' * 64, 0
    for line in path.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        checksum = record.pop('sha256')
        if record['previous'] != previous or digest(record) != checksum:
            raise KitError('Cadena de auditoría alterada.')
        previous, count = checksum, count + 1
    return {'events_verified': count, 'last_sha256': previous,
            'limits': 'Integridad por hash; no es una firma ni protección frente al administrador del equipo.'}


@contextmanager
def transaction(root):
    with state_lock(root):
        verify_audit(root)
        state = deepcopy(load(root))
        yield state
        save(root, state)
