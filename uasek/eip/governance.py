"""Explicit levels, single-use scoped approvals and reviewed policy changes."""
import datetime as dt
from pathlib import Path
import re
import uuid

from . import store
from ..common import KitError, now, read_json, redact_data, safe_path, write_json
from ..context_format import digest

READ = {'read', 'search', 'plan', 'quality'}
MATRIX = {
    'consultivo': READ,
    'supervisado': READ | {'memory.write', 'plan.write'},
    'semiautonomo': READ | {'memory.write', 'plan.write', 'execute', 'integrate', 'model.invoke', 'recovery.restore'},
    'autonomo_controlado': READ | {'memory.write', 'plan.write', 'execute', 'integrate', 'model.invoke', 'recovery.restore', 'deploy.staging'},
}
CRITICAL = {'policy.change', 'extension.install', 'lesson.approve', 'conflict.resolve',
            'deploy.production', 'gates.change', 'models.change'}
ACTIONS = set.union(*MATRIX.values()) | CRITICAL


def policy(root):
    value = read_json(store.location(root, 'policy.json'))
    validate_policy(value)
    return value


def validate_policy(value):
    if not isinstance(value, dict) or set(value) != set(store.initial_policy()) or type(value.get('schema_version')) is not int or value.get('schema_version') != 1 or value.get('level') not in MATRIX:
        raise KitError('Política incompatible o nivel de autonomía desconocido.')
    for name, maximum in [('max_workers', 16), ('max_attempts', 5), ('max_timeout_seconds', 3600), ('max_jobs_per_run', 1000), ('max_units_per_run', 1_000_000)]:
        if type(value[name]) is not int or not 1 <= value[name] <= maximum:
            raise KitError('Límite de política inválido: ' + name)
    if type(value['native_reviewed_code']) is not bool or value['container_network'] != 'none':
        raise KitError('Ejecutor nativo debe declararse; los contenedores no admiten red en esta versión.')
    for name in ('allowed_tools', 'allowed_container_images'):
        if not isinstance(value[name], list) or any(not isinstance(v, str) for v in value[name]):
            raise KitError('Lista de política inválida: ' + name)
    if any(not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', tool) for tool in value['allowed_tools']):
        raise KitError('Identificador de herramienta inválido.')
    if any(not re.fullmatch(r'[a-zA-Z0-9./:_-]+@sha256:[a-f0-9]{64}', image) for image in value['allowed_container_images']):
        raise KitError('Las imágenes de contenedor deben estar fijadas por SHA-256.')


def scope(root, action, resource):
    if action not in ACTIONS:
        raise KitError('Acción no reconocida: ' + action)
    return digest({'project_id': store.load(root)['project_id'], 'local_root':str(Path(root).resolve()), 'policy': policy(root),
                   'action': action, 'resource': resource})


def grant(root, action, resource, reviewer, reason, confirmed=False, expires_seconds=600):
    if not confirmed or not reviewer.strip() or not reason.strip():
        raise KitError('La aprobación requiere --approve, revisor y motivo explícitos.')
    if type(expires_seconds) is not int or not 1 <= expires_seconds <= 3600:
        raise KitError('Caducidad de aprobación inválida.')
    with store.transaction(root):
        ident = 'AP-' + uuid.uuid4().hex
        approval = {'id': ident, 'scope': scope(root, action, resource), 'action': action,
                    'resource': resource, 'reviewer': reviewer, 'reason': reason, 'used': False,
                    'expires_at': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=expires_seconds)).isoformat()}
        write_json(safe_path(root, '.uasek/eip/approvals/' + ident + '.json'), redact_data(approval))
        store.audit(root, 'approval.grant', {'id': ident, 'action': action, 'reviewer': reviewer, 'resource': resource})
    return {'approval': ident, 'action': action, 'resource': resource, 'expires_at': approval['expires_at']}


def authorize(root, action, resource, approval=None):
    """Called while holding project lock. Approvals cannot be transferred or reused."""
    settings = policy(root)
    if action not in ACTIONS:
        raise KitError('Acción no reconocida.')
    if action in MATRIX[settings['level']] and action not in CRITICAL:
        return {'level': settings['level'], 'approval': None}
    if not approval or not re.fullmatch(r'AP-[a-f0-9]{32}', approval):
        raise KitError('Permiso denegado; requiere aprobación para ' + action + ' sobre ' + resource)
    path = safe_path(root, '.uasek/eip/approvals/' + approval + '.json')
    record = read_json(path)
    if record.get('used') or record.get('scope') != scope(root, action, resource):
        raise KitError('Aprobación consumida o fuera del proyecto, política o recurso autorizado.')
    if dt.datetime.fromisoformat(record['expires_at']) <= dt.datetime.now(dt.timezone.utc):
        raise KitError('Aprobación caducada.')
    record['used'] = True
    write_json(path, record)
    store.audit(root, 'approval.consume', {'id': approval, 'action': action, 'resource': resource})
    return {'level': settings['level'], 'approval': approval}


def configure(root, category, proposed, approval=None):
    if redact_data(proposed) != proposed:
        raise KitError('La configuración contiene un posible secreto; no se almacenará.')
    if category == 'policy':
        validate_policy(proposed)
        action = 'policy.change'
    elif category == 'gates':
        from .quality import validate_config
        validate_config(proposed)
        action = 'gates.change'
    elif category == 'models':
        from .routing import validate_models
        validate_models(proposed)
        action = 'models.change'
    else:
        raise KitError('Configuración desconocida.')
    resource = digest(proposed)
    with store.transaction(root):
        authorize(root, action, resource, approval)
        write_json(store.location(root, category + '.json'), proposed)
        store.audit(root, action, {'new_sha256': resource})
    return {'configured': category, 'sha256': resource}
