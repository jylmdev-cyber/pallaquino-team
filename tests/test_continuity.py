"""Round-trip context, actual recovery and economical deterministic coordination."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
import zipfile

from uasek import checkpoints, context_format, memory, operations, orchestration, providers
from uasek.cli import main
from uasek.common import KitError, read_json, write_json


class Continuity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'project'
        operations.init_project(self.root, 'Proyecto portable')
        (self.root / 'app.py').write_bytes(b'value = 1\n')

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--root', str(self.root), *args])
        return code, json.loads(stdout.getvalue()) if stdout.getvalue() else None

    def point(self):
        return checkpoints.create(self.root, 'Antes del cambio', 'El comportamiento anterior puede recuperarse')

    def test_neutral_context_excludes_adapter_state_and_preserves_domain(self):
        state = memory.load(self.root)
        state['decisions'] = ['El dominio conserva su contrato.']
        state['architecture'] = 'CLI modular'
        memory.save(self.root, state)
        task = memory.add_task(self.root, 'Continuar', 'tech-lead', 'Preservar contratos')
        providers.switch(self.root, 'claude')
        exported = read_json(self.root / context_format.CONTEXT_PATH)
        self.assertNotIn('provider', exported['state'])
        self.assertNotIn('instructions', exported['state'])
        self.assertEqual(exported['state']['decisions'], state['decisions'])
        self.assertEqual(exported['state']['tasks'][0]['id'], task['id'])
        target = self.base / 'receiver'
        operations.init_project(target, 'Receptor')
        providers.switch(target, 'gemini')
        context_format.import_context(target, self.root / context_format.CONTEXT_PATH)
        received = memory.load(target)
        self.assertEqual(received['provider']['name'], 'gemini')
        self.assertEqual(received['decisions'], state['decisions'])
        self.assertEqual(received['tasks'][0]['id'], task['id'])

    def test_corrupt_or_future_context_rejected(self):
        payload = context_format.envelope(memory.load(self.root))
        for change in ({'format_version':2}, {'state_sha256':'bad'}, {'format':'other'}):
            with self.assertRaises(KitError):
                context_format.validate({**payload, **change})
        payload['state']['provider'] = {'name':'injected','mode':'api'}
        payload['state_sha256'] = context_format.digest(payload['state'])
        with self.assertRaises(KitError):
            context_format.validate(payload)

    def test_import_rejects_malformed_facts_before_writing(self):
        target = self.base / 'receiver'
        operations.init_project(target, 'Receptor')
        original = (target / memory.MEMORY).read_bytes()
        payload = context_format.envelope(memory.load(self.root))
        payload['state']['history'] = [123]
        payload['state_sha256'] = context_format.digest(payload['state'])
        filename = self.base / 'malformed.json'
        write_json(filename, payload)
        with self.assertRaises(KitError):
            context_format.import_context(target, filename)
        self.assertEqual((target / memory.MEMORY).read_bytes(), original)

    def test_import_never_silently_replaces_existing_memory(self):
        payload = context_format.envelope(memory.load(self.root))
        filename = self.base / 'context.json'
        write_json(filename, payload)
        state = memory.load(self.root)
        state['decisions'] = ['Decisión local previa']
        memory.save(self.root, state)
        with self.assertRaises(KitError):
            context_format.import_context(self.root, filename)
        result = context_format.import_context(self.root, filename, replace=True)
        record = checkpoints.inspect(self.root, result['previous_checkpoint'])
        self.assertEqual(record['state']['decisions'], ['Decisión local previa'])
        self.assertEqual(memory.load(self.root)['decisions'], [])

    def test_import_treats_requirements_as_existing_work(self):
        filename = self.base / 'context.json'
        write_json(filename, context_format.envelope(memory.load(self.root)))
        state = memory.load(self.root)
        state['project']['functional_requirements'] = ['Conservar registro de pedidos.']
        memory.save(self.root, state)
        with self.assertRaises(KitError):
            context_format.import_context(self.root, filename)

    def test_import_reports_unverified_evidence_and_rejects_traversal(self):
        task = memory.add_task(self.root, 'Done', 'qa-engineer', 'Evidencia')
        (self.root / 'evidence.txt').write_text('Local')
        memory.update_task(self.root, task['id'], 'done', ['evidence.txt'])
        payload = context_format.envelope(memory.load(self.root))
        filename = self.base / 'context.json'
        write_json(filename, payload)
        target = self.base / 'receiver'
        operations.init_project(target, 'Nuevo')
        result = context_format.import_context(target, filename, dry_run=True)
        self.assertEqual(result['unverified_evidence'][0]['path'], 'evidence.txt')
        payload['state']['tasks'][0]['evidence'] = ['../outside.txt']
        payload['state_sha256'] = context_format.digest(payload['state'])
        write_json(filename, payload)
        with self.assertRaises(KitError):
            context_format.import_context(target, filename)

    def test_checkpoint_captures_code_decisions_and_expectation(self):
        state = memory.load(self.root)
        state['decisions'] = ['Mantener compatibilidad.']
        memory.save(self.root, state)
        result = self.point()
        record = checkpoints.inspect(self.root, result['id'])
        self.assertEqual(record['decisions'], state['decisions'])
        self.assertEqual(record['files']['app.py'], hashlib.sha256(b'value = 1\n').hexdigest())
        self.assertIn('recuperarse', record['expected_outcome'])
        self.assertFalse(record['tests_fresh_and_passing'])

    def test_checkpoint_distinguishes_fresh_stale_and_missing_tests(self):
        point = self.point()
        self.assertFalse(point['tests_fresh_and_passing'])
        folder = self.root / 'tests'
        folder.mkdir()
        (folder / 'test_ok.py').write_text('import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        operations.test_run(self.root)
        self.assertTrue(self.point()['tests_fresh_and_passing'])
        (self.root / 'app.py').write_text('value = 2\n')
        self.assertFalse(self.point()['tests_fresh_and_passing'])

    def test_recovery_restores_old_source_without_touching_current(self):
        result = self.point()
        (self.root / 'app.py').write_text('raise RuntimeError("broken")\n')
        destination = self.base / 'recovery'
        checkpoints.restore(self.root, result['id'], destination)
        self.assertEqual((destination / 'app.py').read_text(), 'value = 1\n')
        self.assertIn('broken', (self.root / 'app.py').read_text())
        self.assertTrue((destination / 'project-memory/RECOVERY.json').exists())
        self.assertFalse((destination / '.git').exists())
        with self.assertRaises(KitError):
            checkpoints.restore(self.root, result['id'], destination)
        with self.assertRaises(KitError):
            checkpoints.restore(self.root, result['id'], self.root / 'nested')

    def test_checkpoint_metadata_and_snapshot_tampering_rejected(self):
        result = self.point()
        folder = checkpoints.checkpoint_path(self.root, result['id'])
        path = folder / 'checkpoint.json'
        original = read_json(path)
        changed = {**original, 'expected_outcome':'Alterado'}
        write_json(path, changed)
        with self.assertRaises(KitError):
            checkpoints.inspect(self.root, result['id'])
        write_json(path, original)
        (folder / 'sources.zip').write_bytes(b'not-a-zip')
        with self.assertRaises(KitError):
            checkpoints.inspect(self.root, result['id'])

    def test_untrusted_snapshot_rejects_zip_slip_even_with_recomputed_checksums(self):
        result = self.point()
        folder = checkpoints.checkpoint_path(self.root, result['id'])
        snapshot = io.BytesIO()
        with zipfile.ZipFile(snapshot, 'w') as archive:
            archive.writestr('../escape.txt', 'outside')
        (folder / 'sources.zip').write_bytes(snapshot.getvalue())
        record = read_json(folder / 'checkpoint.json')
        record['files'] = {'../escape.txt':hashlib.sha256(b'outside').hexdigest()}
        record['snapshot_sha256'] = hashlib.sha256(snapshot.getvalue()).hexdigest()
        record.pop('record_sha256')
        record['record_sha256'] = context_format.digest(record)
        write_json(folder / 'checkpoint.json', record)
        with self.assertRaises(KitError):
            checkpoints.restore(self.root, result['id'], self.base / 'unsafe')
        self.assertFalse((self.base / 'unsafe').exists())
        self.assertFalse((self.base / 'escape.txt').exists())

    def test_snapshots_exclude_secrets_and_do_not_nest_prior_snapshots(self):
        (self.root / '.env').write_text('private')
        first = self.point()
        second = self.point()
        record = checkpoints.inspect(self.root, second['id'])
        self.assertIn('.env', record['omitted'])
        self.assertNotIn('.env', record['files'])
        self.assertFalse(any(checkpoints.DIRECTORY in path for path in record['files']))
        self.assertEqual(len(checkpoints.list_checkpoints(self.root)), 2)

    def test_dry_runs_leave_project_unchanged(self):
        before = {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.point_preview = checkpoints.create(self.root, 'Preview', 'No cambiar', dry_run=True)
        proposal = orchestration.plan(self.root, 'Documentar README')
        orchestration.apply(self.root, proposal, dry_run=True)
        context_format.export(self.root, dry_run=True)
        after = {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_small_documentation_change_selects_one_role(self):
        proposal = orchestration.plan(self.root, 'Documentar README y corregir una frase')
        self.assertEqual([step['role'] for step in proposal['steps']], ['documentation-engineer'])
        self.assertEqual(proposal['execution_policy']['model_calls'], 0)

    def test_security_and_data_work_selects_relevant_roles_with_budget(self):
        proposal = orchestration.plan(self.root, 'Agregar API de autenticación con base de datos SQL', max_roles=4)
        roles = [step['role'] for step in proposal['steps']]
        self.assertEqual(set(roles), {'security-engineer','backend-engineer','database-architect','qa-engineer'})
        self.assertLessEqual(len(roles), 4)
        self.assertTrue(all(step['reasons'] for step in proposal['steps']))

    def test_path_signals_and_sequential_dependencies(self):
        proposal = orchestration.plan(self.root, 'Corregir interacción', paths=['src/view.tsx'])
        self.assertIn('frontend-engineer', [step['role'] for step in proposal['steps']])
        for index, step in enumerate(proposal['steps']):
            self.assertEqual(step['depends_on_steps'], [index] if index else [])
        with self.assertRaises(KitError):
            orchestration.plan(self.root, 'Fix', paths=['../outside.tsx'])

    def test_apply_is_idempotent_and_checkpoints_before_changing_memory(self):
        proposal = orchestration.plan(self.root, 'Agregar endpoint API')
        with patch('uasek.providers.http_json') as remote:
            first = orchestration.apply(self.root, proposal)
            second = orchestration.apply(self.root, proposal)
            remote.assert_not_called()
        self.assertEqual(first['task_ids'], second['task_ids'])
        self.assertTrue(second['already_applied'])
        self.assertEqual(len(memory.load(self.root)['tasks']), len(proposal['steps']))
        record = checkpoints.inspect(self.root, first['checkpoint'])
        self.assertEqual(record['state']['tasks'], [])
        ready = memory.ready(memory.load(self.root))
        self.assertEqual(len(ready), 1)

    def test_budget_cannot_drop_required_quality_or_security_on_apply(self):
        proposal = orchestration.plan(self.root, 'Agregar API de pagos', max_roles=1)
        with self.assertRaises(KitError):
            orchestration.apply(self.root, proposal)
        self.assertEqual(memory.load(self.root)['tasks'], [])
        self.assertFalse((self.root / checkpoints.DIRECTORY).exists())

    def test_modified_plan_or_receipt_does_not_create_duplicate_work(self):
        proposal = orchestration.plan(self.root, 'Actualizar documentación')
        changed = copy.deepcopy(proposal)
        changed['steps'][0]['role'] = 'release-manager'
        with self.assertRaises(KitError):
            orchestration.apply(self.root, changed)
        result = orchestration.apply(self.root, proposal)
        state = memory.load(self.root)
        state['tasks'][0]['title'] = 'Título manipulado'
        memory.save(self.root, state)
        with self.assertRaises(KitError):
            orchestration.apply(self.root, proposal)
        self.assertEqual(len(memory.load(self.root)['tasks']), 1)

    def test_audit_plan_does_not_authorize_or_run_git(self):
        with patch('uasek.operations.run') as process:
            proposal = orchestration.plan(self.root, 'Auditar repositorio')
            process.assert_not_called()
        self.assertTrue(any(step['authorization_required'] for step in proposal['steps']))

    def test_new_cli_commands_and_universal_export(self):
        code, result = self.cli('checkpoint', 'create', '--label', 'CLI', '--expected', 'Restaurar')
        self.assertEqual(code, 0)
        self.assertEqual(self.cli('checkpoint', 'verify', '--id', result['id'])[0], 0)
        self.assertEqual(self.cli('checkpoint', 'list')[0], 0)
        self.assertEqual(self.cli('orchestrate', '--request', 'Documentar README', '--apply')[0], 0)
        self.assertEqual(self.cli('context', 'export')[0], 0)
        self.assertTrue((self.root / context_format.CONTEXT_PATH).exists())


if __name__ == '__main__':
    unittest.main()
