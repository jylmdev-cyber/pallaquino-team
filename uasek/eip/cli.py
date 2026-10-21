"""Engineering platform CLI, added without changing legacy commands."""
from pathlib import Path
import hashlib

from . import brain, engine, extensions, governance, operations, projects, quality, repository, routing, store, transfer
from .. import checkpoints
from ..common import KitError, read_json
from ..context_format import digest

ACTIONS = ['init', 'status', 'policy', 'configure', 'approve', 'brain-add', 'search', 'lesson-review', 'plan',
    'trace', 'relate', 'consistency', 'map', 'quality', 'job-add', 'jobs', 'run', 'review', 'resolve',
    'recover', 'route', 'extension-install', 'registry-add', 'projects', 'ops', 'verify-audit',
    'transfer-export', 'transfer-import', 'restore']


def legacy_scope(args, root):
    if args.command == 'platform' or not store.location(root, 'state.json').exists():
        return None
    action = None
    if args.command in {'docs', 'backup', 'release', 'handoff'}:
        action = 'memory.write'
    elif args.command == 'init':
        action = 'plan.write'
    elif args.command == 'test':
        action = 'execute'
    elif args.command == 'task' and args.action in {'add','update'}:
        action = 'memory.write'
    elif args.command == 'context' and args.action in {'update','import','export'}:
        action = 'memory.write'
    elif args.command == 'checkpoint' and args.action in {'create','restore'}:
        action = 'recovery.restore' if args.action == 'restore' else 'memory.write'
    elif args.command == 'provider' and args.action in {'switch','generate'}:
        action = 'model.invoke' if args.action == 'generate' else 'memory.write'
    elif args.command == 'agent' and args.action == 'brief':
        action = 'plan.write'
    elif args.command == 'orchestrate' and args.apply:
        action = 'plan.write'
    if getattr(args, 'dry_run', False):
        action = None
    if args.output and not getattr(args, 'dry_run', False):
        action = action or 'memory.write'
    if not action:
        return None
    arguments = {key: value for key, value in vars(args).items() if key not in {'platform_approval','policy_preview','verbose'}}
    from ..operations import source_fingerprint
    if action in {'execute', 'model.invoke'}:
        arguments['source_fingerprint'] = source_fingerprint(root)
    for key in ('file', 'prompt_file'):
        value = getattr(args, key, None)
        if value and Path(value).is_file():
            arguments[key + '_sha256'] = hashlib.sha256(Path(value).read_bytes()).hexdigest()
    return {'permission': action, 'resource': 'legacy:' + digest(arguments)}


def authorize_legacy(root, scope, approval):
    if scope:
        with store.transaction(root):
            try:
                governance.authorize(root, scope['permission'], scope['resource'], approval)
            except KitError:
                store.audit(root, 'legacy.denied', scope)
                raise
            store.audit(root, 'legacy.authorized', scope)


def attach(subparsers):
    p = subparsers.add_parser('platform', help='Engineering Intelligence Platform: cerebro, ejecución, permisos y operaciones.')
    p.add_argument('action', choices=ACTIONS)
    p.add_argument('--file', help='Contrato o configuración JSON; en transfer-import, contexto JSON.')
    p.add_argument('--category', choices=['policy', 'gates', 'models'])
    p.add_argument('--id', help='Trabajo, nodo, lección o checkpoint según acción.')
    p.add_argument('--kind', help='Tipo de registro/nodo.')
    p.add_argument('--text')
    p.add_argument('--query')
    p.add_argument('--request', help='Solicitud para selección explicada de agentes.')
    p.add_argument('--max-roles', type=int, default=4)
    p.add_argument('--limit', type=int, default=8)
    p.add_argument('--source', action='append', default=[], help='Evidencia del registro, relativa al proyecto.')
    p.add_argument('--path', help='Archivo de nodo de trazabilidad.')
    p.add_argument('--title', default='')
    p.add_argument('--from-id', dest='from_id')
    p.add_argument('--to-id', dest='to_id')
    p.add_argument('--relation')
    p.add_argument('--evidence', action='append', default=[])
    p.add_argument('--permission', choices=sorted(governance.ACTIONS))
    p.add_argument('--resource', help='Digest/recurso exacto devuelto por previsualización o trabajo.')
    p.add_argument('--reviewer')
    p.add_argument('--reason')
    p.add_argument('--approve', action='store_true', help='Confirmación humana explícita para crear una aprobación acotada.')
    p.add_argument('--approval', help='ID de aprobación de uso único, cuando se requiera.')
    p.add_argument('--expires-seconds', type=int, default=600)
    p.add_argument('--approvals-file', help='JSON con claves execute:J-id, integrate:J-id, deploy.production:J-id, model.invoke:J-id.')
    p.add_argument('--max-workers', type=int, default=2)
    p.add_argument('--max-seconds', type=float, default=120)
    p.add_argument('--max-units', type=float, default=100)
    p.add_argument('--decision', choices=['accept', 'retry', 'discard'])
    p.add_argument('--registry', help='Ruta explícita al catálogo multiproyecto, sin credenciales.')
    p.add_argument('--destination', help='HTML local para ops o carpeta nueva para restore.')
    p.add_argument('--dry-run', action='store_true')


def required(value, flag):
    if value is None:
        raise KitError('Falta ' + flag)
    return value


def dispatch(args, root):
    action, dry = args.action, args.dry_run
    approval = args.approval
    if action == 'init':
        return {'policy': store.initial_policy(), 'dry_run': True} if dry else store.initialize(root)
    store.load(root)
    if action in {'status', 'jobs'}:
        data = operations.snapshot(root)
        return data['jobs'] if action == 'jobs' else data
    if action == 'policy':
        return {'policy': governance.policy(root), 'matrix': {k: sorted(v) for k, v in governance.MATRIX.items()}, 'always_reviewed': sorted(governance.CRITICAL)}
    if action == 'plan':
        from ..orchestration import plan
        proposal = plan(root,required(args.request,'--request'),max_roles=args.max_roles)
        return {'selection':proposal,'execution':'Definir trabajos con reads/writes y quality gates; solo esos contratos pueden ejecutarse en paralelo.'}
    if action == 'verify-audit':
        return store.verify_audit(root)
    if action == 'configure':
        category = required(args.category, '--category')
        proposed = read_json(required(args.file, '--file'))
        if category == 'policy':
            governance.validate_policy(proposed)
        elif category == 'gates':
            quality.validate_config(proposed)
        else:
            routing.validate_models(proposed)
        if dry:
            return {'action': {'policy':'policy.change','gates':'gates.change','models':'models.change'}[category],
                    'resource': digest(proposed), 'proposed': proposed, 'dry_run': True}
        return governance.configure(root, category, proposed, approval)
    if action == 'approve':
        permission, resource = required(args.permission, '--permission'), required(args.resource, '--resource')
        if dry:
            return {'permission': permission, 'resource': resource, 'dry_run': True}
        return governance.grant(root, permission, resource, required(args.reviewer, '--reviewer'),
            required(args.reason, '--reason'), args.approve, args.expires_seconds)
    if action == 'search':
        return brain.search(root, required(args.query, '--query'), args.limit)
    if action == 'consistency':
        return brain.consistency(root)
    if action == 'map':
        return repository.project_map(root)
    if action == 'route':
        return routing.select(root, read_json(required(args.file, '--file')))
    if action == 'quality':
        result = quality.evaluate(root, args.evidence, quality.project_gates(root))
        return {**result, 'exit_code': 0 if result['passed'] else 1}
    if action == 'transfer-export':
        if dry:
            return {**transfer.export(root,True),'permission':'memory.write','resource':transfer.PATH}
        with store.transaction(root):
            governance.authorize(root,'memory.write',transfer.PATH,approval)
            result = transfer.export(root)
            store.audit(root,'brain.export',{'path':transfer.PATH})
        return result
    if action == 'transfer-import':
        return transfer.import_context(root, required(args.file, '--file'), approval, dry)
    if action == 'extension-install':
        manifest = extensions.validate(read_json(required(args.file, '--file')))
        if dry:
            return {'permission': 'extension.install', 'resource': digest(manifest), 'manifest': manifest, 'dry_run': True}
        return extensions.install(root, manifest, approval)
    if action == 'job-add':
        spec = engine.normalize_spec(root, read_json(required(args.file, '--file')))
        if dry:
            return {'spec': spec, 'execution_resource': engine.execution_resource(root, spec), 'dry_run': True}
        return engine.add_job(root, spec, approval)
    if action == 'run':
        approvals = read_json(args.approvals_file) if args.approvals_file else {}
        if not isinstance(approvals, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in approvals.items()):
            raise KitError('Mapa de aprobaciones inválido.')
        if dry:
            return {'jobs': operations.snapshot(root)['jobs'], 'max_workers': args.max_workers,
                    'max_seconds': args.max_seconds, 'max_units': args.max_units, 'permission':'plan.write',
                    'resource':engine.run_resource(root,args.max_workers,args.max_seconds,args.max_units), 'execution': False, 'dry_run': True}
        result = engine.run(root, args.max_workers, args.max_seconds, args.max_units, approvals)
        statuses = list(result['jobs'].values())
        result['exit_code'] = 1 if 'failed' in statuses else (3 if any(s not in {'done','discarded'} for s in statuses) else 0)
        return result
    if action == 'ops':
        return operations.render(root, required(args.destination, '--destination'), dry, approval)
    if action == 'projects':
        return projects.list_projects(required(args.registry, '--registry'))
    if action == 'restore':
        ident, destination = required(args.id, '--id'), required(args.destination, '--destination')
        preview = checkpoints.restore(root, ident, destination, dry_run=True)
        resource = digest({'checkpoint': ident, 'destination': str(Path(destination).resolve())})
        if dry:
            return {**preview, 'permission': 'recovery.restore', 'resource': resource}
        with store.transaction(root):
            governance.authorize(root, 'recovery.restore', resource, approval)
            result = checkpoints.restore(root, ident, destination)
            store.audit(root, 'recovery.stage', {'checkpoint': ident, 'destination': result['destination']})
        return result
    if dry:
        return {'action': action, 'execution': False, 'dry_run': True}
    if action == 'brain-add':
        return brain.add_record(root, required(args.kind, '--kind'), required(args.text, '--text'), args.source, approval)
    if action == 'lesson-review':
        return brain.approve_lesson(root, required(args.id, '--id'), approval)
    if action == 'trace':
        return brain.trace(root, required(args.id, '--id'), required(args.kind, '--kind'), required(args.path, '--path'), args.title, approval)
    if action == 'relate':
        return brain.relate(root, required(args.from_id, '--from-id'), required(args.to_id, '--to-id'), required(args.relation, '--relation'), approval)
    if action == 'review':
        return engine.integrate(root, required(args.id, '--id'), approval)
    if action == 'resolve':
        return engine.resolve(root, required(args.id, '--id'), required(args.decision, '--decision'), approval)
    if action == 'recover':
        return engine.recover(root)
    if action == 'registry-add':
        path = required(args.registry, '--registry')
        with store.transaction(root):
            governance.authorize(root, 'plan.write', str(Path(path).resolve()), approval)
            store.audit(root, 'registry.register', {'registry': str(Path(path).resolve())})
        return projects.register(path, root)
    raise KitError('Acción no implementada.')
