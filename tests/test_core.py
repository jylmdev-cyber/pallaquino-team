"""Behavioral and adversarial checks in isolated temporary projects."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from uasek import memory, operations, providers
from uasek.cli import main, context_update
from uasek.common import (KIT_ROOT, KitError, files, http_json, read_json, redact,
                          safe_path, state_lock, write_json)


class ProjectCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'project'
        operations.init_project(self.root, 'Prueba', 'Proyecto temporal')

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, title='Implementar', dependencies=()):
        return memory.add_task(self.root, title, 'backend-engineer', 'Resultado observable', dependencies)

    def evidence(self):
        path = self.root / 'result.txt'
        path.write_text('Caso observado: correcto', encoding='utf-8')
        return path.name

    def cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['--root', str(self.root), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_init_never_overwrites(self):
        (self.root / 'important.txt').write_text('conservar')
        with self.assertRaises(KitError):
            operations.init_project(self.root, 'Otro')
        self.assertEqual((self.root / 'important.txt').read_text(), 'conservar')

    def test_init_dry_run_creates_nothing(self):
        path = self.base / 'new'
        operations.init_project(path, 'Nuevo', dry_run=True)
        self.assertFalse(path.exists())

    def test_adopt_existing_only_adds_memory(self):
        path = self.base / 'legacy'
        path.mkdir()
        (path / 'README.md').write_text('Original')
        (path / 'app.py').write_text('original_code = True')
        operations.init_project(path, 'Heredado', existing=True)
        self.assertEqual((path / 'README.md').read_text(), 'Original')
        self.assertEqual((path / 'app.py').read_text(), 'original_code = True')
        self.assertTrue((path / memory.MEMORY).is_file())
        with self.assertRaises(KitError):
            operations.init_project(path, 'Otra memoria', existing=True)

    def test_template_selection_and_invalid_template(self):
        path = self.base / 'school'
        operations.init_project(path, 'Escuela', template='enrollment')
        self.assertIn('capacidad concurrente', (path / 'docs/SYSTEM_REFERENCE.md').read_text(encoding='utf-8'))
        with self.assertRaises(KitError):
            operations.init_project(self.base / 'escape', 'X', template='../../outside')
        self.assertFalse((self.base / 'escape').exists())

    def test_dependency_blocks_execution_and_completion(self):
        first = self.task()
        second = self.task('Validar', [first['id']])
        for state in ('in_progress', 'done'):
            with self.assertRaises(KitError):
                memory.update_task(self.root, second['id'], state, [self.evidence()])
        self.assertEqual([t['id'] for t in memory.ready(memory.load(self.root))], [first['id']])

    def test_completion_requires_real_internal_evidence(self):
        task = self.task()
        for evidence in ([], ['missing.txt'], ['../outside.txt']):
            with self.assertRaises(KitError):
                memory.update_task(self.root, task['id'], 'done', evidence)
        memory.update_task(self.root, task['id'], 'done', [self.evidence()])
        self.assertEqual(memory.load(self.root)['tasks'][0]['status'], 'done')

    def test_cannot_reopen_prerequisite_of_completed_task(self):
        first = self.task()
        memory.update_task(self.root, first['id'], 'done', [self.evidence()])
        second = self.task('QA', [first['id']])
        memory.update_task(self.root, second['id'], 'in_progress')
        with self.assertRaises(KitError):
            memory.update_task(self.root, first['id'], 'todo')

    def test_unknown_agent_or_dependency_rejected(self):
        with self.assertRaises(KitError):
            memory.add_task(self.root, 'X', 'unknown', 'Y')
        with self.assertRaises(KitError):
            self.task(dependencies=['T9000'])

    def test_dry_run_does_not_change_memory_or_create_lock(self):
        before = (self.root / memory.MEMORY).read_bytes()
        self.cli('task', 'add', '--title', 'X', '--acceptance', 'Y', '--dry-run')
        self.cli('provider', 'switch', '--provider', 'gemini', '--dry-run')
        self.cli('handoff', '--dry-run')
        self.cli('docs', '--dry-run')
        self.assertEqual((self.root / memory.MEMORY).read_bytes(), before)
        self.assertFalse((self.root / '.uasek').exists())
        self.assertFalse((self.root / 'docs').exists())

    def test_lock_prevents_lost_updates(self):
        with state_lock(self.root):
            with self.assertRaises(KitError):
                self.task()
        self.assertFalse((self.root / '.uasek/state.lock').exists())

    def test_context_update_rejects_secret_and_reserved_fields(self):
        filename = self.base / 'patch.json'
        for value in ({'tasks': []}, {'architecture': 'password=' + 'dangerous-value-123'}, {'next_actions': [1]}):
            write_json(filename, value)
            with self.assertRaises(KitError):
                context_update(self.root, filename, False)

    def test_context_partial_project_update_preserves_name(self):
        filename = self.base / 'patch.json'
        write_json(filename, {'project': {'description': 'Actualizado'}, 'decisions': ['Usar biblioteca estándar.']})
        context_update(self.root, filename, False)
        state = memory.load(self.root)
        self.assertEqual(state['project']['name'], 'Prueba')
        self.assertEqual(state['project']['description'], 'Actualizado')
        self.assertIn('biblioteca estándar', (self.root / 'project-memory/DECISIONS.md').read_text(encoding='utf-8'))

    def test_handoff_redacts_memory_secrets_and_omits_environment_files(self):
        secret = 'sk-' + 'a' * 30
        state = memory.load(self.root)
        state['decisions'] = ['private credential ' + secret]
        memory.save(self.root, state)
        (self.root / '.env').write_text('MY_PRIVATE_VALUE=do-not-export')
        memory.handoff(self.root)
        text = (self.root / 'project-memory/AI_HANDOFF.md').read_text(encoding='utf-8')
        self.assertNotIn(secret, text)
        self.assertNotIn('do-not-export', text)
        self.assertIn('REDACTED', text)
        self.assertEqual(sum(line.startswith('## ') for line in text.splitlines()), 10)

    def test_provider_switch_preserves_tasks_and_decisions(self):
        self.task()
        before = memory.load(self.root)
        providers.switch(self.root, 'claude')
        after = memory.load(self.root)
        self.assertEqual(before['tasks'], after['tasks'])
        self.assertEqual(before['decisions'], after['decisions'])
        self.assertEqual(after['provider']['name'], 'claude')
        with self.assertRaises(KitError):
            providers.switch(self.root, 'openai', 'api')

    def test_brief_contains_contract_and_acceptance(self):
        task = self.task()
        result = memory.brief(self.root, task['id'])
        text = Path(result['path']).read_text(encoding='utf-8')
        self.assertIn('Resultado observable', text)
        self.assertIn('backend-engineer', text)

    def test_audit_requires_permission_before_git_invocation(self):
        with patch('uasek.operations.run') as command:
            with self.assertRaises(KitError):
                operations.audit(self.root)
            command.assert_not_called()

    @unittest.skipUnless(__import__('shutil').which('git'), 'Git no disponible')
    def test_git_audit_does_not_change_worktree(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True, capture_output=True)
        (self.root / 'work.txt').write_text('uncommitted')
        subprocess.run(['git', 'add', 'work.txt'], cwd=self.root, check=True, capture_output=True)
        before = subprocess.run(['git', 'status', '--porcelain'], cwd=self.root, capture_output=True).stdout
        index = (self.root / '.git/index').read_bytes()
        report = operations.audit(self.root, True, True)
        after = subprocess.run(['git', 'status', '--porcelain'], cwd=self.root, capture_output=True).stdout
        self.assertEqual(before, after)
        self.assertEqual((self.root / '.git/index').read_bytes(), index)
        self.assertTrue(all('--no-optional-locks' in c['command'] and 'core.fsmonitor=false' in c['command'] for c in report['checks']))
        self.assertTrue(report['read_only'])
        self.assertFalse((self.root / '.uasek').exists())

    def test_security_returns_locations_never_secret_values(self):
        secret = 'ghp_' + 'z' * 30
        (self.root / 'unsafe.txt').write_text(secret)
        (self.root / '.env').write_text('password=' + 'example-real-value')
        report = operations.scan(self.root)
        self.assertTrue(any(f['rule'] == 'provider-token' for f in report['findings']))
        self.assertTrue(any(f['rule'] == 'sensitive-file' for f in report['findings']))
        self.assertNotIn(secret, json.dumps(report))

    def test_scanner_reports_large_file_coverage(self):
        (self.root / 'large.txt').write_bytes(b'x' * 1_000_001)
        self.assertIn('large.txt', operations.scan(self.root)['skipped'])

    def test_walker_ignores_dependency_directories(self):
        path = self.root / 'node_modules/untrusted'
        path.mkdir(parents=True)
        (path / 'x.txt').write_text('x')
        self.assertNotIn('x.txt', [p.name for p in files(self.root)])

    def test_symlink_cannot_escape_project(self):
        external = self.base / 'external'
        external.mkdir()
        (external / 'private.txt').write_text('outside')
        try:
            (self.root / 'link').symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest('SO no permite crear symlink sin privilegios')
        self.assertNotIn('private.txt', [p.name for p in files(self.root)])
        with self.assertRaises(KitError):
            safe_path(self.root, 'link/private.txt')

    def test_backup_excludes_credentials_and_verifies_hashes(self):
        import hashlib
        (self.root / 'normal.txt').write_text('normal')
        (self.root / '.env').write_text('private')
        (self.root / 'embedded.txt').write_text('sk-' + 'b' * 30)
        output = self.base / 'snapshot.zip'
        result = operations.backup(self.root, output)
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read('MANIFEST.json'))
            self.assertNotIn('project/.env', archive.namelist())
            self.assertNotIn('project/embedded.txt', archive.namelist())
            for relative, checksum in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read('project/' + relative)).hexdigest(), checksum)
        self.assertIn('.env', result['omitted'])
        with self.assertRaises(KitError):
            operations.backup(self.root, output)

    def test_docs_preserves_manual_and_updates_generated(self):
        path = self.root / 'docs/PROJECT_OVERVIEW.md'
        path.parent.mkdir()
        path.write_text('Edición humana', encoding='utf-8')
        result = operations.generate_docs(self.root)
        self.assertIn('docs/PROJECT_OVERVIEW.md', result['preserved_manual'])
        self.assertEqual(path.read_text(encoding='utf-8'), 'Edición humana')
        state = memory.load(self.root)
        state['architecture'] = 'Arquitectura validada'
        memory.save(self.root, state)
        operations.generate_docs(self.root)
        self.assertIn('Arquitectura validada', (self.root / 'docs/architecture/SYSTEM_ARCHITECTURE.md').read_text(encoding='utf-8'))

    def test_dependency_coverage_is_never_silently_clean(self):
        (self.root / 'requirements.txt').write_text('requests>=2\nPyYAML==5.3\n')
        code, stdout, _ = self.cli('dependency')
        result = json.loads(stdout)
        self.assertEqual(code, 3)
        self.assertEqual(result['checks'][0]['status'], 'not_queried')
        self.assertTrue(result['unresolved'])

    def test_dependency_osv_request_and_vulnerable_exit(self):
        (self.root / 'requirements.txt').write_text('PyYAML==5.3\n')
        with patch('uasek.operations.http_json', return_value={'vulns': [{'id': 'TEST-VULN'}]}) as request:
            code, stdout, _ = self.cli('dependency', '--online')
        self.assertEqual(code, 1)
        self.assertEqual(request.call_args.args[1]['package'], {'name':'PyYAML', 'ecosystem':'PyPI'})
        self.assertIn('TEST-VULN', stdout)

    def test_network_failure_is_error_not_clean(self):
        (self.root / 'requirements.txt').write_text('demo==1.0.0\n')
        with patch('uasek.operations.http_json', side_effect=OSError('network down')):
            code, stdout, _ = self.cli('dependency', '--online')
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stdout)['checks'][0]['status'], 'error')

    def test_npm_lock_scoped_and_nested_packages(self):
        write_json(self.root / 'package-lock.json', {'lockfileVersion':3,'packages':{
            '':{'name':'app','version':'1.0.0'},
            'node_modules/@scope/item':{'version':'2.0.0'},
            'node_modules/top/node_modules/sub':{'version':'1.2.3'}}})
        entries, unresolved = operations.dependency_inventory(self.root)
        self.assertEqual({e['name'] for e in entries}, {'@scope/item', 'sub'})
        self.assertFalse(unresolved)

    def test_stack_offline_has_no_invented_version(self):
        with patch('uasek.operations.http_json') as request:
            result = operations.stack_check('pypi', 'pip')
        self.assertIsNone(result['version'])
        request.assert_not_called()

    def test_stack_online_uses_registry_result(self):
        with patch('uasek.operations.http_json', return_value={'info':{'version':'9.8.7'}}):
            result = operations.stack_check('pypi', 'example', True)
        self.assertEqual(result['version'], '9.8.7')
        self.assertIsNotNone(result['verified_at'])

    def test_test_runner_zero_tests_fails(self):
        (self.root / 'tests').mkdir()
        result = operations.test_run(self.root)
        self.assertEqual(result['tests_ran'], 0)
        self.assertNotEqual(result['returncode'], 0)

    def test_test_runner_propagates_failure_and_records_evidence(self):
        folder = self.root / 'tests'
        folder.mkdir()
        (folder / 'test_failure.py').write_text('import unittest\nclass Case(unittest.TestCase):\n def test_fail(self): self.fail("expected")\n')
        result = operations.test_run(self.root)
        self.assertEqual(result['tests_ran'], 1)
        self.assertNotEqual(result['returncode'], 0)
        self.assertEqual(read_json(self.root / '.uasek/last-test.json')['returncode'], result['returncode'])

    def test_release_requires_tests_and_complete_tasks(self):
        with self.assertRaises(KitError):
            operations.release(self.root, '1.0.0')
        write_json(self.root / '.uasek/last-test.json', {'returncode':0,'tests_ran':1})
        self.task()
        with self.assertRaises(KitError):
            operations.release(self.root, '1.0.0')

    def test_release_prepares_local_report_only(self):
        folder = self.root / 'tests'
        folder.mkdir()
        (folder / 'test_ok.py').write_text('import unittest\nclass Case(unittest.TestCase):\n def test_ok(self): self.assertEqual(2+2,4)\n')
        operations.test_run(self.root)
        result = operations.release(self.root, '1.0.0')
        self.assertEqual(result['status'], 'prepared_for_human_review')
        self.assertTrue((self.root / 'dist/release-1.0.0.json').is_file())
        self.assertFalse((self.root / '.git').exists())

    def test_invalid_release_versions_rejected(self):
        for version in ('../escape', '01.2.3', '1.2', 'v1.2.3'):
            with self.assertRaises(KitError):
                operations.release(self.root, version)

    def test_packaging_metadata_does_not_change_source_fingerprint(self):
        before = operations.source_fingerprint(self.root)
        write_json(self.root / 'PACKAGE_MANIFEST.json', {'files':{}})
        self.assertEqual(before, operations.source_fingerprint(self.root))
        (self.root / 'app.py').write_text('changed = True')
        self.assertNotEqual(before, operations.source_fingerprint(self.root))

    def test_release_rejects_source_modified_after_test(self):
        folder = self.root / 'tests'
        folder.mkdir()
        path = folder / 'test_ok.py'
        path.write_text('import unittest\nclass Case(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        operations.test_run(self.root)
        path.write_text(path.read_text() + '\n# Changed after test\n')
        with self.assertRaisesRegex(KitError, 'cambió'):
            operations.release(self.root, '1.0.0')

    def test_agent_result_checks_evidence_without_executing_commands(self):
        task = self.task()
        evidence = self.evidence()
        result = {'task_id':task['id'],'summary':'Completado para revisión', 'artifacts':[evidence],
                  'checks':[{'command':['do-not-execute'],'returncode':0,'evidence':evidence}],
                  'risks':[],'next_actions':[]}
        path = self.root / 'result.json'
        write_json(path, result)
        self.assertTrue(memory.validate_result(self.root, path)['structurally_valid'])
        self.assertEqual(memory.load(self.root)['tasks'][0]['status'], 'todo')
        for change in ({'returncode':1}, {'evidence':'../outside.txt'}, {'command':'shell command'}):
            invalid = {**result, 'checks':[{**result['checks'][0], **change}]}
            write_json(path, invalid)
            with self.assertRaises(KitError):
                memory.validate_result(self.root, path)

    def test_output_never_overwrites_existing_file(self):
        path = self.base / 'report.json'
        path.write_text('retain')
        code, _, _ = self.cli('--output', str(path), 'doctor')
        self.assertEqual(code, 2)
        self.assertEqual(path.read_text(), 'retain')

    def test_cli_missing_memory_returns_error(self):
        path = self.root / memory.MEMORY
        path.unlink()
        self.assertEqual(self.cli('status')[0], 2)

    def test_invalid_json_returns_error_without_traceback(self):
        (self.root / memory.MEMORY).write_text('{broken')
        self.assertEqual(self.cli('status')[0], 2)

    def test_corrupt_memory_and_cycles_are_reported(self):
        path = self.root / memory.MEMORY
        write_json(path, [])
        with self.assertRaises(KitError):
            memory.load(self.root)
        memory.save(self.root, memory.initial('Cycle'))
        first = self.task()
        second = self.task('Second', [first['id']])
        state = memory.load(self.root)
        state['tasks'][0]['depends_on'] = [second['id']]
        memory.save(self.root, state)
        with self.assertRaisesRegex(KitError, 'Ciclo'):
            memory.load(self.root)


class ProviderAndContracts(unittest.TestCase):
    def test_adapter_rejects_remote_or_credential_endpoint(self):
        credentials = 'http://' + 'user:pass' + '@localhost:11434'
        for endpoint in ('http://example.org', credentials, 'https://localhost', 'http://localhost/path'):
            with self.assertRaises(KitError):
                providers.generate_local('model', 'test', endpoint)

    def test_ollama_payload_and_text_only_response(self):
        with patch('uasek.providers.http_json', return_value={'response':'print("hello")','done':True}) as request:
            result = providers.generate_local('test-model', 'Hello')
        self.assertEqual(request.call_args.args[1], {'model':'test-model','prompt':'Hello','stream':False})
        self.assertIn('print', result['response'])
        self.assertIn('no se ejecuta', result['execution'])

    def test_ollama_invalid_response_is_rejected(self):
        with patch('uasek.providers.http_json', return_value={'error':'model missing'}):
            with self.assertRaises(KitError):
                providers.generate_local('missing', 'test')

    def test_catalog_references_and_agent_skills_resolve(self):
        catalog = read_json(KIT_ROOT / 'configs/catalog.json')
        self.assertEqual(len(catalog), 30)
        for item in catalog:
            self.assertTrue((KIT_ROOT / item['path']).is_file(), item['path'])
        skills = {p.parent.name for p in (KIT_ROOT / 'skills').glob('*/*/SKILL.md')}
        contracts = memory.agents()
        self.assertEqual(len(contracts), 21)
        for contract in contracts.values():
            self.assertTrue(set(contract['skills']) <= skills)
            for key in ('identity','role','objectives','responsibilities','allowed_tools', 'required_inputs',
                        'deliverables','restrictions','acceptance_criteria','communication','escalation','handoff'):
                self.assertTrue(contract[key])

    def test_all_17_tool_entrypoints_show_help(self):
        tools = sorted((KIT_ROOT / 'tools').glob('*.py'))
        self.assertEqual(len(tools), 17)
        for tool in tools:
            result = subprocess.run([sys.executable, str(tool), '--help'], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, tool.name)
            self.assertIn(b'usage:', result.stdout)

    def test_redaction_does_not_expose_environment_credential(self):
        with patch.dict(os.environ, {'TEST_API_KEY':'a-private-value-5678'}):
            self.assertNotIn('a-private-value-5678', redact('value=a-private-value-5678'))

    def test_redaction_preserves_json_and_removes_key_block(self):
        from uasek.common import redact_data
        sample = 'a-sensitive-value'
        result = redact_data({'secret':sample,'nested':{'note':'password=' + 'value-to-hide-123'}})
        self.assertEqual(json.loads(json.dumps(result))['secret'], '[REDACTED]')
        self.assertNotIn('value-to-hide-123', json.dumps(result))
        key = '-----BEGIN ' + 'PRIVATE KEY-----\nbase64data\n-----END ' + 'PRIVATE KEY-----'
        self.assertNotIn('base64data', redact(key))


class LocalHTTP(unittest.TestCase):
    def test_http_client_with_real_local_server(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"response":"local-fixture","done":true}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            result = providers.generate_local('fixture', 'hello', f'http://127.0.0.1:{server.server_port}')
            self.assertEqual(result['response'], 'local-fixture')
            self.assertEqual(received[0]['model'], 'fixture')
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
