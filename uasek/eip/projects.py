"""Explicit multi-project registry; no shared project memories or credentials."""
from pathlib import Path
from . import store
from ..common import KitError, read_json, state_lock, write_json


def register(registry, root):
    registry, root = Path(registry).resolve(), Path(root).resolve()
    state = store.load(root)
    registry.parent.mkdir(parents=True, exist_ok=True)
    with state_lock(registry.parent):
        data = read_json(registry, {'schema_version': 1, 'projects': []})
        if data.get('schema_version') != 1:
            raise KitError('Registro de proyectos incompatible.')
        for item in data['projects']:
            old = Path(item['root']).resolve()
            if item['project_id'] == state['project_id'] and old != root:
                raise KitError('Identidad duplicada en otra ruta; no se mezclarán clones como proyectos distintos.')
            if old != root and (old.is_relative_to(root) or root.is_relative_to(old)):
                raise KitError('Raíces de proyectos anidadas se rechazan para evitar compartir archivos.')
            if old == root:
                if item['project_id'] != state['project_id']:
                    raise KitError('La identidad del proyecto cambió; requiere revisión del registro.')
                return {'registered': item, 'already_registered': True}
        item = {'project_id': state['project_id'], 'root': str(root)}
        data['projects'].append(item)
        write_json(registry, data)
    return {'registered': item, 'already_registered': False}


def list_projects(registry):
    data = read_json(registry)
    if data.get('schema_version') != 1:
        raise KitError('Registro de proyectos incompatible.')
    results = []
    for item in data['projects']:
        root = Path(item['root'])
        state = store.load(root)
        if state['project_id'] != item['project_id']:
            raise KitError('La raíz registrada apunta a otra identidad de proyecto.')
        results.append({**item, 'jobs': len(state['jobs']), 'level': read_json(store.location(root, 'policy.json'))['level']})
    return results
