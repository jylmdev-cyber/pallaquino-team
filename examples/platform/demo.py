"""Run two reviewed, independent jobs without a model or remote service."""
import argparse
from pathlib import Path
import sys

# Allows use from the source ZIP; an installed uasek package works too.
root = Path(__file__).resolve().parents[2]
if (root / 'uasek').exists():
    sys.path.insert(0, str(root))
from uasek import operations
from uasek.eip import engine, governance, store
from uasek.eip.operations import render


def demo(destination, confirmed=False):
    if not confirmed:
        raise ValueError('Use --approve-demo para autorizar exclusivamente los scripts de esta demostración local.')
    project = Path(destination).resolve()
    operations.init_project(project, 'Demostración Engineering Intelligence Platform')
    store.initialize(project)
    approvals = {}
    for name in ('frontend', 'backend'):
        source = 'from pathlib import Path\nimport time\ntime.sleep(.2)\nPath(' + repr(name+'.txt') + ').write_text("OK '+name+'",encoding="utf-8")\n'
        (project / (name+'.py')).write_text(source,encoding='utf-8')
        spec = {'id':'J-'+name,'title':'Implementar '+name,'acceptance':'Entregar texto OK y pasar regresión',
            'agent':'auto','reads':[name+'.py'],'writes':[name+'.txt'],
            'command':{'tool':'python','args':[name+'.py']},'reviewed_code':True,
            'gates':[{'id':'expected','kind':'file_contains','mandatory':True,'paths':[name+'.txt'],'value':'OK'},
                {'id':'regression','kind':'command','mandatory':True,'tool':'python',
                 'args':['-c','from pathlib import Path; assert Path('+repr(name+'.txt')+').read_text().startswith("OK")']}]}
        job = engine.add_job(project,spec)
        approvals['execute:'+job['id']] = governance.grant(project,'execute',job['execution_resource'],
            'Operador de demo','--approve-demo autoriza scripts locales conocidos',True)['approval']
    run = engine.run(project,max_workers=2,approvals=approvals)
    for job in store.load(project)['jobs']:
        approval = governance.grant(project,'integrate',engine.review_resource(project,job),
            'Operador de demo','Revisión de entregables OK de la demo local',True)['approval']
        engine.integrate(project,job['id'],approval)
    dashboard = render(project,'OPERATIONS.html')
    return {'project':str(project),'peak_parallel_workers':run['peak_parallel_workers'],
        'jobs':{j['id']:j['status'] for j in store.load(project)['jobs']},'operations':dashboard['path']}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',required=True)
    parser.add_argument('--approve-demo',action='store_true')
    args = parser.parse_args()
    print(json.dumps(demo(args.destination,args.approve_demo),ensure_ascii=False,indent=2))
