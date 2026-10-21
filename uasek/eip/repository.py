"""Static project graph: Python AST plus explicitly marked lexical adapters."""
import ast
import json
from pathlib import Path
import re
import tomllib

from ..common import files, is_sensitive, redact


def project_map(root):
    root = Path(root).resolve()
    modules, edges, configurations, tests, entries, errors, unsupported = [], [], [], [], [], [], []
    module_names = {}
    for path in files(root):
        relative = path.relative_to(root).as_posix()
        if relative.startswith('project-memory/') or is_sensitive(path) or path.stat().st_size > 1_000_000:
            continue
        if '/tests/' in '/' + relative or path.name.startswith('test_'):
            tests.append(relative)
        if path.suffix in {'.toml', '.json', '.yml', '.yaml', '.ini'} or path.name in {'Dockerfile', 'requirements.txt'}:
            configurations.append(relative)
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            continue
        if path.name == 'pyproject.toml':
            try:
                data = tomllib.loads(text)
                entries.extend({'source': relative, 'name': key, 'target': value} for key, value in data.get('project', {}).get('scripts', {}).items())
                edges.extend({'from': relative, 'to': value, 'kind': 'declared-dependency'} for value in data.get('project', {}).get('dependencies', []))
            except (ValueError, TypeError) as exc:
                errors.append({'file': relative, 'error': type(exc).__name__})
        if path.name == 'package.json':
            try:
                data = json.loads(text)
                entries.extend({'source': relative, 'name': key, 'target': redact(value), 'executed': False} for key, value in data.get('scripts', {}).items())
                edges.extend({'from': relative, 'to': name, 'kind': 'declared-dependency'} for name in data.get('dependencies', {}))
            except (ValueError, TypeError) as exc:
                errors.append({'file': relative, 'error': type(exc).__name__})
        if path.suffix == '.py':
            name = relative[:-3].replace('/', '.')
            if name.endswith('.__init__'):
                name = name[:-9]
            module_names[name] = relative
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError as exc:
                errors.append({'file': relative, 'error': 'SyntaxError', 'line': exc.lineno})
                continue
            contracts, imports = [], []
            package = name if path.name == '__init__.py' else name.rpartition('.')[0]
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    record = {'name': node.name, 'line': node.lineno, 'kind': type(node).__name__}
                    if hasattr(node, 'args'):
                        record['parameters'] = [arg.arg for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
                        record['returns'] = ast.unparse(node.returns) if node.returns else None
                    record['decorators'] = [ast.unparse(d) for d in node.decorator_list]
                    contracts.append(record)
                elif isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ''
                    if node.level:
                        parts = package.split('.') if package else []
                        parts = parts[:max(0, len(parts)-node.level+1)]
                        base = '.'.join(parts + ([base] if base else []))
                    imports.append(base)
                    imports.extend(base + '.' + alias.name for alias in node.names)
                elif isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
                    if ast.unparse(node.test) in {"__name__ == '__main__'", "'__main__' == __name__"}:
                        entries.append({'source': relative, 'target': '__main__', 'line': node.lineno})
            modules.append({'path': relative, 'name': name, 'language': 'python', 'adapter': 'python-ast', 'contracts': contracts})
            edges.extend({'from': relative, 'to': name, 'kind': 'import'} for name in sorted(set(imports)) if name)
        elif path.suffix in {'.js', '.jsx', '.ts', '.tsx', '.mjs'}:
            imports = re.findall(r'''(?:from\s*|require\(\s*|import\s*)["']([^"']+)["']''', text)
            contracts = re.findall(r'\bexport\s+(?:default\s+)?(?:async\s+)?(?:function|class|const)\s+(\w+)', text)
            modules.append({'path': relative, 'language': 'javascript/typescript', 'adapter': 'lexical-not-a-parser', 'contracts': contracts})
            edges.extend({'from': relative, 'to': name, 'kind': 'lexical-import'} for name in imports)
        elif path.suffix in {'.go', '.rs', '.java', '.cs', '.php', '.rb'}:
            unsupported.append({'file': relative, 'reason': 'Requiere adaptador específico; inventario sin inferir relaciones.'})
    for edge in edges:
        if edge['kind'] == 'import':
            target = edge['to']
            while target and target not in module_names:
                target = target.rpartition('.')[0]
            edge['resolved_path'] = module_names.get(target)
    return {'format': 'uasek.repository-map', 'version': 1, 'modules': modules, 'relations': edges,
            'entry_points': entries, 'tests': tests, 'configurations': configurations,
            'parse_errors': errors, 'unsupported': unsupported,
            'executed_repository_code': False, 'limits': 'AST Python y heurísticas JS/TS; imports dinámicos y reflexión no se resuelven completamente.'}
