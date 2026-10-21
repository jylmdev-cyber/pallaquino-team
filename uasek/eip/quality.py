"""Deterministic, configurable gates used by both task closure and the engine."""
import ast
from pathlib import Path

from . import store
from ..common import KitError, is_sensitive, read_json, redact, safe_path

KINDS = {'files_exist', 'python_syntax', 'no_secrets', 'file_contains', 'command'}


def validate_gates(gates):
    if not isinstance(gates, list) or not gates:
        raise KitError('Se requiere una lista no vacía de quality gates.')
    ids = set()
    for gate in gates:
        if not isinstance(gate, dict) or gate.get('kind') not in KINDS or not isinstance(gate.get('id'), str) or not gate['id'] or type(gate.get('mandatory')) is not bool:
            raise KitError('Contrato de quality gate inválido.')
        if gate['id'] in ids:
            raise KitError('ID de quality gate duplicado.')
        ids.add(gate['id'])
        if 'paths' in gate and (not isinstance(gate['paths'], list) or any(not isinstance(p, str) for p in gate['paths'])):
            raise KitError('Rutas de quality gate inválidas.')
        if gate['kind'] == 'file_contains' and (not isinstance(gate.get('value'), str) or not gate.get('paths')):
            raise KitError('file_contains requiere paths y value.')
        if gate['kind'] == 'command' and (not isinstance(gate.get('tool'), str) or not gate['tool'] or not isinstance(gate.get('args'), list) or any(not isinstance(v, str) for v in gate['args'])):
            raise KitError('Gate de regresión requiere herramienta declarada y argumentos estructurados.')


def project_gates(root):
    value = read_json(store.location(root, 'gates.json'))
    validate_config(value)
    return value['gates']


def validate_config(value):
    if not isinstance(value,dict) or set(value) != {'schema_version','gates'} or type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise KitError('Versión de quality gates desconocida.')
    validate_gates(value['gates'])


def evaluate(workspace, evidence, gates, command_runner=None):
    validate_gates(gates)
    checks = []
    for gate in gates:
        passed, detail = True, []
        paths = gate.get('paths', evidence)
        if gate['kind'] == 'command':
            if command_runner is None:
                passed, detail = False, ['Regresión no ejecutada; requiere el motor y permisos de ejecución.']
            else:
                result = command_runner(gate['tool'], gate['args'])
                passed = result['returncode'] == 0
                detail = [result]
        else:
            if not paths:
                passed, detail = False, ['Sin archivos de evidencia.']
            for relative in paths:
                path = safe_path(workspace, relative)
                if not path.is_file() or is_sensitive(path):
                    passed = False
                    detail.append({'file': relative, 'error': 'missing-or-sensitive'})
                    continue
                if path.stat().st_size > 5_000_000:
                    passed = False
                    detail.append({'file': relative, 'error': 'file-too-large-for-gate'})
                    continue
                if gate['kind'] == 'files_exist':
                    continue
                try:
                    text = path.read_text(encoding='utf-8')
                except UnicodeError:
                    passed = False
                    detail.append({'file': relative, 'error': 'not-text'})
                    continue
                if gate['kind'] == 'python_syntax' and path.suffix == '.py':
                    try:
                        ast.parse(text)
                    except SyntaxError as exc:
                        passed = False
                        detail.append({'file': relative, 'line': exc.lineno, 'error': 'SyntaxError'})
                elif gate['kind'] == 'no_secrets' and redact(text) != text:
                    passed = False
                    detail.append({'file': relative, 'error': 'possible-secret-values-not-printed'})
                elif gate['kind'] == 'file_contains' and gate['value'] not in text:
                    passed = False
                    detail.append({'file': relative, 'error': 'required-content-missing'})
        checks.append({'id': gate['id'], 'mandatory': gate['mandatory'], 'passed': passed, 'details': detail})
    return {'passed': all(c['passed'] for c in checks if c['mandatory']), 'checks': checks}


def require_completion(root, task, evidence):
    if not store.location(root, 'state.json').exists():
        return
    state = store.load(root)
    bound = [job for job in state['jobs'] if job['spec'].get('memory_task') == task['id']]
    if bound and any(job['status'] != 'done' for job in bound):
        raise KitError('La tarea tiene trabajos de plataforma sin integrar o con gates incumplidos.')
    if bound:
        from .engine import file_hash
        for job in bound:
            expected = {**job.get('base', {}), **job.get('outputs', {})}
            if any(file_hash(root, path) != checksum for path, checksum in expected.items()):
                raise KitError('Las entradas/entregables cambiaron desde la validación del trabajo; repetir regresión.')
    gates = project_gates(root)
    # Command gates must have succeeded in a bound engine job; do not execute code in legacy task mutation.
    if any(gate['kind'] == 'command' and gate['mandatory'] for gate in gates):
        if not bound or any(not job.get('quality', {}).get('passed') for job in bound):
            raise KitError('Los quality gates de comandos requieren evidencia del motor.')
        gates = [g for g in gates if g['kind'] != 'command']
    if gates and not evaluate(root, evidence, gates)['passed']:
        raise KitError('Quality gates obligatorios incumplidos; no se cerrará la tarea.')
