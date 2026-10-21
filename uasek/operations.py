"""Read-only analysis, opt-in remote checks and controlled local artifacts."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib
import urllib.parse
import zipfile

from .common import (KIT_ROOT, RESOURCE_ROOT, KitError, SECRET_PATTERNS, atomic_write, files,
                     http_json, is_sensitive, now, read_json, redact, run,
                     safe_path, state_lock, write_json)
from . import memory


def analyze(root):
    counts, manifests, total = Counter(), [], 0
    for path in files(root):
        total += 1
        counts[path.suffix or '(sin extensión)'] += 1
        if path.name in {'package.json', 'pyproject.toml', 'Cargo.toml', 'go.mod',
                          'pom.xml', 'requirements.txt', 'Gemfile', 'composer.json'}:
            manifests.append(path.relative_to(root).as_posix())
    return {'root': str(root), 'files': total, 'extensions': dict(counts),
            'manifests': manifests, 'memory_present': safe_path(root, memory.MEMORY).exists(),
            'note': 'Inventario; no ejecuta código ni deduce requisitos de negocio.'}


def scan(root):
    findings, skipped, inspected = [], [], 0
    for path in files(root):
        rel = path.relative_to(root).as_posix()
        if is_sensitive(path):
            findings.append({'file': rel, 'line': 0, 'severity': 'high',
                             'rule': 'sensitive-file', 'action': 'Excluir del repositorio y verificar exposición.'})
            continue
        if path.stat().st_size > 1_000_000:
            skipped.append(rel)
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            skipped.append(rel)
            continue
        if '\x00' in content:
            skipped.append(rel)
            continue
        inspected += 1
        for line_number, line in enumerate(content.splitlines(), 1):
            for rule, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({'file': rel, 'line': line_number, 'severity': 'high',
                                     'rule': rule, 'action': 'Validar; si es real, rotar y retirar con autorización.'})
            if re.search(r'\bDEBUG\s*=\s*(?:True|true|1)\b', line):
                findings.append({'file': rel, 'line': line_number, 'severity': 'medium',
                                 'rule': 'debug-enabled', 'action': 'Desactivar en configuración de producción.'})
            if path.name.lower().startswith('dockerfile') and re.search(r'^FROM\s+\S+:latest\s*$', line, re.I):
                findings.append({'file': rel, 'line': line_number, 'severity': 'medium',
                                 'rule': 'container-latest', 'action': 'Fijar versión y digest verificado.'})
    return {'at': now(), 'kind': 'heuristic-static-scan', 'inspected': inspected,
            'findings': findings, 'skipped': skipped,
            'limitations': 'No es SAST completo, prueba de penetración ni garantía de ausencia de secretos. No analiza binarios, archivos >1 MB ni directorios excluidos. Nunca imprime valores detectados.'}


def audit(root, authorized=False, full=False):
    if not authorized:
        raise KitError('Auditoría Git requiere --authorize. Opciones: completa (--full), rápida, rechazar o sin Git.')
    if not shutil.which('git'):
        raise KitError('Git no está instalado.')
    # Git status can otherwise launch a repository-configured fsmonitor program.
    prefix = ['git', '--no-pager', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c',
              'core.untrackedCache=false', '-c', 'log.showSignature=false',
              '-c', 'core.hooksPath=', '-c', 'diff.external=']

    def inspect_git(argv):
        return run(prefix + argv[1:], root)

    check = inspect_git(['git', 'rev-parse', '--show-toplevel'])
    if check['returncode']:
        raise KitError('La carpeta no pertenece a un repositorio Git.')
    commands = [
        ['git', 'status', '--short', '--branch'],
        ['git', 'branch', '--show-current'],
        ['git', 'log', '-5', '--oneline'],
        ['git', 'diff', '--no-ext-diff', '--no-textconv', '--name-only', '--diff-filter=U'],
        ['git', 'ls-files', '--others', '--ignored', '--exclude-standard'],
    ]
    checks = [inspect_git(command) for command in commands]
    report = {'at': now(), 'mode': 'full' if full else 'quick', 'read_only': True,
              'checks': checks, 'inventory': analyze(root), 'security': scan(root),
              'tests': 'No ejecutadas: auditar no ejecuta código del repositorio.',
              'dependencies': 'Inventario local; OSV requiere dependency --online explícito.'}
    if full:
        report['tracked_sensitive_paths'] = [p for p in inspect_git(['git', 'ls-files'])['stdout'].splitlines() if is_sensitive(p)]
        report['commit_convention_sample'] = inspect_git(['git', 'log', '-20', '--format=%s'])['stdout']
        report['ci_files'] = [p.relative_to(root).as_posix() for p in files(root)
                              if '.github/workflows/' in p.as_posix() or p.name in {'.gitlab-ci.yml', 'Jenkinsfile'}]
        report['limits'] = 'No escanea historial de blobs, submódulos ni remotos; full amplía metadatos locales, no es auditoría exhaustiva.'
    return report


def dependency_inventory(root):
    entries, unsupported = [], []
    req = safe_path(root, 'requirements.txt')
    if req.exists():
        for line in req.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)(?:\s*;.*)?', line)
            if match:
                if ';' in line:
                    unsupported.append({'source': 'requirements.txt', 'reason': 'Marcador de entorno no evaluado; entrada consultada conservadoramente.'})
                entries.append({'name': match[1], 'version': match[2], 'ecosystem': 'PyPI'})
            else:
                unsupported.append({'source': 'requirements.txt', 'reason': 'Entrada no fijada o sintaxis avanzada; no resuelta.'})
    pyproject = safe_path(root, 'pyproject.toml')
    if pyproject.exists():
        config = tomllib.loads(pyproject.read_text(encoding='utf-8-sig'))
        deps = list(config.get('project', {}).get('dependencies', []))
        for group in config.get('project', {}).get('optional-dependencies', {}).values():
            deps.extend(group)
        for line in deps:
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)', line)
            if match:
                entries.append({'name': match[1], 'version': match[2], 'ecosystem': 'PyPI'})
            else:
                unsupported.append({'source': 'pyproject.toml', 'reason': 'Dependencia no fijada o avanzada; no resuelta.'})
    lock = safe_path(root, 'package-lock.json')
    if lock.exists():
        data = read_json(lock)
        if data.get('lockfileVersion') not in (2, 3):
            unsupported.append({'source': 'package-lock.json', 'reason': 'Solo lock v2/v3.'})
        for location, item in data.get('packages', {}).items():
            if not location or 'node_modules/' not in location:
                continue
            name = item.get('name') or location.rsplit('node_modules/', 1)[-1]
            if item.get('version') and re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?', item['version']):
                entries.append({'name': name, 'version': item['version'], 'ecosystem': 'npm'})
            else:
                unsupported.append({'source': 'package-lock.json', 'reason': 'Entrada sin versión semántica (link/Git).'} )
    elif safe_path(root, 'package.json').exists():
        unsupported.append({'source': 'package.json', 'reason': 'Requiere package-lock.json v2/v3 para versiones resueltas.'})
    for path in files(root):
        if path.name in {'poetry.lock', 'uv.lock', 'yarn.lock', 'pnpm-lock.yaml', 'Cargo.lock', 'go.sum', 'pom.xml', 'Gemfile.lock', 'composer.lock'}:
            unsupported.append({'source': path.relative_to(root).as_posix(), 'reason': 'Ecosistema/formato no implementado en el auditor de dependencias.'})
    unique = {(e['ecosystem'], e['name'], e['version']): e for e in entries}
    return list(unique.values()), unsupported


def dependencies(root, online=False):
    entries, unsupported = dependency_inventory(root)
    checks, errors = [], []
    for entry in entries:
        check = {**entry, 'status': 'not_queried', 'vulnerabilities': []}
        if online:
            try:
                result = http_json('https://api.osv.dev/v1/query',
                                   {'package': {'name': entry['name'], 'ecosystem': entry['ecosystem']}, 'version': entry['version']})
                check['vulnerabilities'] = [v['id'] for v in result.get('vulns', [])]
                check['status'] = 'queried'
            except Exception as exc:
                check['status'] = 'error'
                errors.append({'name': entry['name'], 'error': type(exc).__name__})
        checks.append(check)
    return {'at': now(), 'online': online, 'checks': checks, 'unresolved': unsupported, 'errors': errors,
            'coverage': 'Versiones exactas PyPI y package-lock npm v2/v3. No instala ni ejecuta paquetes. Metadatos de paquetes se envían a OSV solo con --online.'}


def stack_check(ecosystem, package, online=False):
    if not re.fullmatch(r'@?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?', package):
        raise KitError('Nombre de paquete inválido.')
    encoded = urllib.parse.quote(package, safe='')
    url = (f'https://pypi.org/pypi/{encoded}/json' if ecosystem == 'pypi'
           else f'https://registry.npmjs.org/{encoded}')
    result = {'package': package, 'ecosystem': ecosystem, 'source': url,
              'verified_at': None, 'version': None, 'status': 'pending_online_verification'}
    if online:
        data = http_json(url)
        result.update(version=data['info']['version'] if ecosystem == 'pypi' else data['dist-tags']['latest'],
                      verified_at=now(), status='registry_metadata_verified')
    result['limits'] = 'La etiqueta latest del registro no demuestra compatibilidad, LTS ni ausencia de vulnerabilidades; comprobar notas oficiales antes de elegir.'
    return result


def init_project(destination, name, description='', template=None, dry_run=False, existing=False):
    destination = Path(destination).resolve()
    if existing and not destination.is_dir():
        raise KitError('--existing requiere una carpeta existente.')
    if existing and safe_path(destination, 'project-memory').exists():
        raise KitError('Ya existe project-memory; se conserva. Use context show/update.')
    if destination.exists() and not existing:
        raise KitError('El destino ya existe; no se sobrescriben proyectos. Use una carpeta nueva.')
    if not name.strip():
        raise KitError('El nombre es obligatorio.')
    source = None
    if template:
        source = safe_path(RESOURCE_ROOT / 'templates/systems', template + '/SYSTEM.md')
        if not source.exists():
            raise KitError('Plantilla desconocida; use catalog.')
    if dry_run:
        return {'destination': str(destination), 'name': name, 'template': template, 'dry_run': True}
    destination.mkdir(parents=True, exist_ok=existing)
    memory.save(destination, memory.initial(name, description))
    if existing:
        return {'destination': str(destination), 'name': name, 'existing': True,
                'note': 'Solo se incorporó project-memory. Auditoría no ejecutada; decisión del propietario pendiente de registrar.'}
    atomic_write(destination / 'README.md', f'# {name}\n\n{description}\n\nMemoria: [project-memory/state.json](project-memory/state.json).\n\nEjecutar herramientas usando la ruta al kit y --root a este proyecto. El kit no impone framework ni genera una aplicación de negocio.\n')
    atomic_write(destination / '.gitignore', '.env\n.env.*\n!.env.example\n.venv/\n__pycache__/\n.uasek/\nbackups/\n')
    atomic_write(destination / '.env.example', '# Agregue nombres de variables; nunca credenciales reales.\n')
    if source:
        atomic_write(destination / 'docs/SYSTEM_REFERENCE.md', source.read_text(encoding='utf-8'))
    return {'destination': str(destination), 'name': name, 'template': template, 'dry_run': False}


def generate_docs(root, dry_run=False):
    state = memory.load(root)
    rendered = {
        'docs/PROJECT_OVERVIEW.md': '# Proyecto\n\n' + state['project']['name'] + '\n\n' + state['project']['description'],
        'docs/architecture/SYSTEM_ARCHITECTURE.md': '# Arquitectura\n\n' + (state['architecture'] or 'No definida. Resolver requisitos y registrar una decisión antes de implementar.'),
        'docs/architecture/TECH_STACK.md': '# Stack\n\n' + json.dumps(state['stack'], ensure_ascii=False, indent=2) + '\n\nSolo incluir versiones verificadas con fecha y fuente. Sin elementos significa sin selección.',
        'docs/continuity/PROJECT_STATUS.md': '# Estado\n\n' + '\n'.join(f"- {t['id']}: {t['status']} — {t['title']}" for t in state['tasks']),
    }
    # Generated files are tool-owned. Human-authored files are left intact.
    marker = '<!-- generated-by-uasek -->\n'
    written, skipped = [], []
    for relative, text in rendered.items():
        path = safe_path(root, relative)
        if path.exists() and not path.read_text(encoding='utf-8').startswith(marker):
            skipped.append(relative)
            continue
        if not dry_run:
            atomic_write(path, marker + redact(text) + '\n')
        written.append(relative)
    return {'generated': written, 'preserved_manual': skipped, 'dry_run': dry_run}


def backup(root, output, dry_run=False):
    """Source snapshot, not production/data backup. No auto-restore."""
    output = Path(output).resolve()
    if output.exists():
        raise KitError('El respaldo ya existe; elija un archivo nuevo.')
    selected, omitted = [], []
    for path in files(root):
        if path == output:
            continue
        rel = path.relative_to(root).as_posix()
        if is_sensitive(path) or path.suffix.lower() in {'.zip', '.sqlite', '.db'}:
            omitted.append(rel)
            continue
        if path.stat().st_size > 5_000_000:
            omitted.append(rel)
            continue
        raw = path.read_bytes()
        try:
            content = raw.decode('utf-8')
        except UnicodeError:
            omitted.append(rel)
            continue
        if '\x00' in content or redact(content) != content:
            omitted.append(rel)
            continue
        selected.append((rel, raw))
    manifest = {'created_at': now(), 'kind': 'source-only', 'files': {
        rel: hashlib.sha256(raw).hexdigest() for rel, raw in selected}, 'omitted': omitted,
        'limits': 'Excluye secretos heurísticos, binarios, bases de datos, archivos >5 MB y directorios ignorados. No sustituye backup cifrado de producción.'}
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents replacing an archive made by another process.
        with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
            for relative, raw in selected:
                archive.writestr('project/' + relative, raw)
            archive.writestr('MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return {'output': str(output), 'included': len(selected), 'omitted': omitted, 'dry_run': dry_run}


def release(root, version, dry_run=False):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?', version):
        raise KitError('Versión inválida; use SemVer X.Y.Z o X.Y.Z-prerelease.')
    state = memory.load(root)
    unfinished = [t['id'] for t in state['tasks'] if t['status'] != 'done']
    if unfinished:
        raise KitError('Tareas pendientes: ' + ', '.join(unfinished))
    test_report = read_json(safe_path(root, '.uasek/last-test.json'), {})
    if test_report.get('returncode') != 0 or not test_report.get('tests_ran'):
        raise KitError('Se requiere test exitoso con al menos una prueba en este proyecto.')
    if test_report.get('source_fingerprint') != source_fingerprint(root):
        raise KitError('El código cambió o falta huella de pruebas. Ejecute test otra vez.')
    if any(f['severity'] == 'high' for f in scan(root)['findings']):
        raise KitError('El escaneo detectó hallazgos altos. Revisar antes de preparar release.')
    output = safe_path(root, f'dist/release-{version}.json')
    if output.exists():
        raise KitError('Ya existe la preparación de esa versión.')
    report = {'version': version, 'prepared_at': now(), 'tasks': len(state['tasks']),
              'test': test_report, 'status': 'prepared_for_human_review',
              'limits': 'No crea tag, commit, paquete ni despliegue. Reejecutar pruebas si cambió código desde el reporte.'}
    if not dry_run:
        write_json(output, report)
    return report


def test_run(root, timeout=120, dry_run=False):
    directory = safe_path(root, 'tests')
    if not directory.is_dir():
        raise KitError('No existe tests/. Este runner usa unittest; ejecute otros runners explícitamente en su entorno.')
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
    if dry_run:
        return {'command': command, 'dry_run': True}
    before = source_fingerprint(root)
    result = run(command, root, timeout)
    match = re.search(r'Ran (\d+) tests?', result['stderr'])
    result.update(at=now(), tests_ran=int(match[1]) if match else 0)
    result['source_fingerprint'] = before
    if source_fingerprint(root) != before:
        result.update(returncode=2, error='El código cambió durante las pruebas; repetir con fuentes estables.')
    if result['tests_ran'] == 0 and result['returncode'] == 0:
        result['returncode'] = 2
        result['error'] = 'No se ejecutó ninguna prueba.'
    write_json(safe_path(root, '.uasek/last-test.json'), result)
    return result


def source_fingerprint(root):
    """Conservative digest of source/config files, excluding documentation and memory."""
    digest = hashlib.sha256()
    for path in sorted(files(root)):
        relative = path.relative_to(root).as_posix()
        if relative == 'PACKAGE_MANIFEST.json' or relative.startswith(('project-memory/', 'ai/handoff/', 'ai/plans/', 'docs/')) or is_sensitive(path):
            continue
        if path.suffix.lower() not in {'.py', '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue', '.css', '.svg', '.json', '.toml', '.yaml', '.yml', '.go', '.rs', '.java', '.cs', '.c', '.h', '.cpp', '.php', '.rb', '.sh', '.ps1', '.sql', '.txt'}:
            continue
        digest.update(relative.encode('utf-8') + b'\x00')
        with path.open('rb') as stream:
            while chunk := stream.read(65536):
                digest.update(chunk)
    return digest.hexdigest()


def doctor(root):
    return {'python': sys.version.split()[0], 'python_supported': sys.version_info >= (3, 11),
            'platform': sys.platform, 'git': shutil.which('git'), 'kit': str(KIT_ROOT),
            'root_exists': root.is_dir(), 'memory': safe_path(root, memory.MEMORY).exists(),
            'dependencies': 'Solo biblioteca estándar; instalación opcional con pip.',
            'network': 'No comprobada; comandos online requieren selección explícita.'}
