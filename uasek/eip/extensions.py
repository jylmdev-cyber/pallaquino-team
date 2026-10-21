"""Reviewed extension manifests. Registration never imports or executes code."""
import re
from . import governance, store
from ..common import KitError, redact_data
from ..context_format import digest


def validate(manifest):
    if redact_data(manifest) != manifest:
        raise KitError('La extensión contiene un posible secreto; usar referencias sin credenciales.')
    required = {'api_version', 'id', 'kind', 'version', 'permissions', 'dependencies', 'capabilities', 'entrypoint'}
    if not isinstance(manifest, dict) or set(manifest) != required or type(manifest['api_version']) is not int or manifest['api_version'] != 1:
        raise KitError('Contrato de extensión incompatible.')
    if not isinstance(manifest['id'], str) or not isinstance(manifest['version'], str) or manifest['id'] == 'python' or not re.fullmatch(r'[a-z][a-z0-9-]{1,63}', manifest['id']) or not re.fullmatch(r'\d+\.\d+\.\d+', manifest['version']):
        raise KitError('ID o versión de extensión inválidos.')
    if manifest['kind'] not in {'agent', 'skill', 'provider', 'tool', 'connector'} or not isinstance(manifest['entrypoint'], str):
        raise KitError('Tipo o entrypoint inválido.')
    for key in ('permissions', 'dependencies', 'capabilities'):
        if not isinstance(manifest[key], list) or any(not isinstance(v, str) for v in manifest[key]):
            raise KitError('Lista inválida en contrato: ' + key)
    if set(manifest['permissions']) - governance.ACTIONS:
        raise KitError('Extensión solicita permisos desconocidos.')
    return manifest


def install(root, manifest, approval=None):
    validate(manifest)
    with store.transaction(root) as state:
        governance.authorize(root, 'extension.install', digest(manifest), approval)
        ids = {item['id'] for item in state['extensions']}
        if manifest['id'] in ids or not set(manifest['dependencies']) <= ids:
            raise KitError('Extensión duplicada o dependencias no satisfechas.')
        state['extensions'].append(manifest)
        store.audit(root, 'extension.install', {'id': manifest['id'], 'version': manifest['version']})
    return {'installed': manifest['id'], 'code_executed': False,
            'limits': 'Registro de contrato; ejecutar un conector nuevo requiere implementar y revisar su adaptador explícitamente.'}
