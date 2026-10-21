"""End-to-end CLI workflow using a temporary business project."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from uasek.common import KIT_ROOT


class CLIWorkflow(unittest.TestCase):
    def test_increment_delivery_and_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'app'
            env = {**os.environ, 'PYTHONIOENCODING':'utf-8'}

            def command(*args, expected=0):
                result = subprocess.run([sys.executable, str(KIT_ROOT / 'kit.py'), *args],
                    cwd=base, env=env, text=True, encoding='utf-8', capture_output=True, timeout=30)
                self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
                return json.loads(result.stdout) if result.stdout.strip() else None

            command('init', '--destination', str(root), '--name', 'Reserva', '--template', 'reservations')

            def at(*args, expected=0):
                return command('--root', str(root), *args, expected=expected)

            self.assertTrue(at('doctor')['memory'])
            self.assertGreater(at('analyze')['files'], 0)
            at('audit', expected=2)
            task = at('task', 'add', '--title', 'Probar flujo', '--agent', 'qa-engineer',
                      '--acceptance', 'Prueba de contrato ejecutable')
            self.assertEqual(at('task', 'ready')[0]['id'], task['id'])
            at('agent', 'brief', '--task', task['id'])
            at('task', 'update', '--id', task['id'], '--status', 'in_progress')
            tests = root / 'tests'
            tests.mkdir()
            (tests / 'test_contract.py').write_text('import unittest\nclass Contract(unittest.TestCase):\n def test_unique(self): self.assertEqual(len(set([1,1])),1)\n')
            report = root / 'evidence.txt'
            report.write_text('Revisión manual: criterios satisfechos en fixture de demostración.')
            result = {'task_id':task['id'],'summary':'Fixture revisado','artifacts':['tests/test_contract.py'],
                      'checks':[{'command':['python','-m','unittest'],'returncode':0,'evidence':'evidence.txt'}],
                      'risks':['Demostración, no aplicación implementada'],'next_actions':[]}
            (root / 'result.json').write_text(json.dumps(result), encoding='utf-8')
            at('agent', 'validate', '--result', str(root / 'result.json'))
            at('task', 'update', '--id', task['id'], '--status', 'done', '--evidence', 'evidence.txt')
            self.assertEqual(at('status')['counts']['done'], 1)
            at('docs')
            at('security')
            at('dependency')
            self.assertIsNone(at('stack', '--package', 'example')['version'])
            self.assertEqual(at('test')['tests_ran'], 1)
            self.assertEqual(at('release', '--version', '1.0.0')['status'], 'prepared_for_human_review')
            at('provider', 'switch', '--provider', 'gemini')
            at('context', 'export')
            self.assertTrue(Path(at('handoff')['path']).is_file())
            output = base / 'sources.zip'
            at('backup', '--destination', str(output))
            self.assertTrue(output.is_file())
            self.assertEqual(at('context', 'show')['provider']['name'], 'gemini')

    def test_startup_menu_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(KIT_ROOT / 'kit.py')], cwd=directory,
                text=True, encoding='utf-8', capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0)
            self.assertIn('¿Qué proyecto vamos a trabajar?', result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
