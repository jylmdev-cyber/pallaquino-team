"""Stable process adapter contract for explicitly installed tools/connectors."""
from pathlib import Path
import shutil
import sys

from . import store
from ..common import KitError, read_json


def catalog(root):
    enabled = read_json(store.location(root, 'policy.json'))['allowed_tools']
    adapters = {'python': {'api_version': 1, 'executable': sys.executable,
                           'container_command': 'python', 'permissions': ['execute']}}
    for manifest in store.load(root)['extensions']:
        if manifest['id'] not in enabled or manifest['kind'] not in {'tool', 'connector'} or not manifest['entrypoint'].startswith('process:'):
            continue
        if 'execute' not in manifest['permissions'] or 'process' not in manifest['capabilities']:
            raise KitError('Adaptador de proceso requiere permisos execute y capacidad process.')
        target = manifest['entrypoint'][8:]
        resolved = str(Path(target).resolve()) if Path(target).is_absolute() else shutil.which(target)
        if not resolved or not Path(resolved).is_file():
            raise KitError('Ejecutable declarado no disponible: ' + manifest['id'])
        adapters[manifest['id']] = {'api_version': 1, 'executable': resolved,
            'container_command': Path(target).name, 'permissions': manifest['permissions'], 'version': manifest['version']}
    return adapters
