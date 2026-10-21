"""Read-only operations snapshot and optional local HTML control center."""
import html
from pathlib import Path

from . import brain, governance, store
from .. import memory
from ..common import atomic_write, now, read_json, redact_data, safe_path
from .engine import review_resource, execution_resource
from ..context_format import digest


def snapshot(root):
    state = store.load(root)
    jobs = []
    for job in state['jobs']:
        jobs.append({'id': job['id'], 'agent': job['spec']['agent'], 'title': job['spec']['title'],
            'status': job['status'], 'reason': job.get('reason'), 'attempts': len(job['attempts']),
            'provider': job.get('provider'), 'model': job.get('model'), 'quality': job.get('quality'),
            'execution_resource': execution_resource(root, job['spec']),
            'diagnosis': job.get('diagnosis'),
            'review_resource': review_resource(root, job) if job['status'] in {'review','conflict','blocked','failed'} else None})
    return redact_data({'at': now(), 'project_id': state['project_id'], 'project': memory.load(root)['project'],
        'policy': governance.policy(root), 'jobs': jobs, 'runs': state['runs'],
        'resources': {'attempts': sum(len(j['attempts']) for j in state['jobs']),
            'units_reserved': sum(r['units_reserved'] for r in state['runs']),
            'model_calls': sum(1 for j in state['jobs'] for a in j['attempts'] if a.get('result', {}).get('measured_tokens') is not None)},
        'documentation': brain.consistency(root), 'audits': memory.load(root)['audits'],
        'last_tests': read_json(safe_path(root, '.uasek/last-test.json'), {}),
        'lessons': [r for r in state['records'] if r['kind'] in {'lesson','pattern'}],
        'extensions': state['extensions']})


def render(root, destination, dry_run=False, approval=None):
    data = snapshot(root)
    path = safe_path(root, destination)
    if path.exists():
        from ..common import KitError
        raise KitError('El centro de operaciones no reemplaza archivos; elija destino nuevo.')
    resource = 'ops:' + digest(str(path))
    if not dry_run:
        escape = lambda value: html.escape(str(value))
        rows = ''.join('<tr>' + ''.join('<td>' + escape(job.get(key, '')) + '</td>' for key in ('id','agent','title','status','attempts','provider','model','reason')) + '</tr>' for job in data['jobs'])
        body = '<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Engineering Intelligence Platform</title>'
        body += '<style>body{font:16px system-ui;margin:3rem;background:#101827;color:#e8efff}h1{font-size:2rem}table{border-collapse:collapse;width:100%}td,th{padding:.8rem;border-bottom:1px solid #40516c;text-align:left}pre{white-space:pre-wrap}input{padding:.6rem;margin:1rem 0}</style>'
        body += '<h1>Engineering Intelligence Platform</h1><h2>' + escape(data['project']['name']) + '</h2><p>Proyecto: ' + escape(data['project_id']) + ' · Autonomía: ' + escape(data['policy']['level']) + '</p>'
        body += '<p>Snapshot local de lectura. No contiene credenciales ni acciones de despliegue.</p><input id="filter" placeholder="Filtrar tareas" aria-label="Filtrar tareas">'
        body += '<table><thead><tr>' + ''.join('<th>'+key+'</th>' for key in ('ID','Agente','Trabajo','Estado','Intentos','Proveedor','Modelo','Bloqueo')) + '</tr></thead><tbody>' + rows + '</tbody></table>'
        for name, value in [('Recursos',data['resources']),('Ejecuciones',data['runs']),('Auditorías',data['audits']),('Documentación y trazabilidad',data['documentation']),('Pruebas',data['last_tests']),('Lecciones',data['lessons'])]:
            import json
            body += '<h2>'+escape(name)+'</h2><pre>'+escape(json.dumps(value,ensure_ascii=False,indent=2))+'</pre>'
        body += '<script>document.querySelector("#filter").addEventListener("input",e=>document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase())))</script></html>'
        with store.transaction(root):
            governance.authorize(root, 'memory.write', resource, approval)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x',encoding='utf-8',newline='\n') as stream:
                stream.write(body)
            store.audit(root,'operations.render',{'path':destination})
    return {'path': str(path), 'project_id': data['project_id'], 'permission':'memory.write', 'resource':resource, 'dry_run': dry_run}
