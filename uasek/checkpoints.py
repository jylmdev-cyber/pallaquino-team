"""Recoverable, source-only checkpoints with integrity and test freshness."""
from contextlib import nullcontext
from copy import deepcopy
import datetime as dt
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import uuid
import zipfile

from . import memory
from .common import (KitError, files, is_sensitive, now, read_json, redact,
                     redact_data, safe_path, state_lock, write_json)
from .context_format import digest
from .operations import source_fingerprint

DIRECTORY = 'project-memory/checkpoints'
MAX_SNAPSHOT = 50_000_000


def checkpoint_path(root, ident):
    if not isinstance(ident, str) or not re.fullmatch(r'CP-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{8}', ident):
        raise KitError('ID de checkpoint inválido.')
    return safe_path(root, DIRECTORY + '/' + ident)


def collect(root):
    entries, omitted, size = {}, [], 0
    for path in files(root):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(DIRECTORY + '/') or relative == 'PACKAGE_MANIFEST.json':
            continue
        if is_sensitive(path) or path.suffix.lower() in {'.zip', '.whl', '.db', '.sqlite', '.pyc'} or path.stat().st_size > 5_000_000:
            omitted.append(relative)
            continue
        raw = path.read_bytes()
        try:
            content = raw.decode('utf-8')
        except UnicodeError:
            omitted.append(relative)
            continue
        if '\x00' in content or redact(content) != content:
            omitted.append(relative)
            continue
        size += len(raw)
        if size > MAX_SNAPSHOT:
            raise KitError('Checkpoint supera 50 MB de fuentes de texto; reducir alcance.')
        entries[relative] = raw
    return entries, omitted


def create(root, label, expected, dry_run=False, locked=False):
    root = Path(root).resolve()
    if not label.strip() or not expected.strip():
        raise KitError('Checkpoint requiere etiqueta y resultado esperado no vacíos.')
    with (nullcontext() if dry_run or locked else state_lock(root)):
        state = deepcopy(memory.load(root))
        before = source_fingerprint(root)
        entries, omitted = collect(root)
        test = redact_data(read_json(safe_path(root, '.uasek/last-test.json'), {}))
        fresh = bool(test.get('returncode') == 0 and test.get('tests_ran', 0) > 0 and test.get('source_fingerprint') == before)
        if source_fingerprint(root) != before or memory.load(root) != state:
            raise KitError('El proyecto cambió mientras se capturaba el checkpoint; repetir.')
        ident = 'CP-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
        record = {'format': 'uasek.checkpoint', 'format_version': 1, 'id': ident, 'created_at': now(),
                  'label': redact(label), 'expected_outcome': redact(expected),
                  'state': redact_data(state), 'decisions': redact_data(state['decisions']),
                  'source_fingerprint': before, 'test_report': test,
                  'tests_fresh_and_passing': fresh, 'omitted': omitted,
                  'files': {p: hashlib.sha256(raw).hexdigest() for p, raw in entries.items()},
                  'limits': 'Fuentes de texto seleccionadas; sin Git, binarios, bases, dependencias ni secretos detectados. No ejecuta pruebas ni restaura producción.'}
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w', zipfile.ZIP_DEFLATED) as archive:
            for relative, raw in entries.items():
                archive.writestr(relative, raw)
        record['snapshot_sha256'] = hashlib.sha256(content.getvalue()).hexdigest()
        record['record_sha256'] = digest(record)
        if not dry_run:
            folder = checkpoint_path(root, ident)
            folder.mkdir(parents=True, exist_ok=False)
            (folder / 'sources.zip').write_bytes(content.getvalue())
            write_json(folder / 'checkpoint.json', record)
        return {'id': ident, 'files': len(entries), 'omitted': omitted,
                'tests_fresh_and_passing': fresh, 'source_fingerprint': before, 'dry_run': dry_run}


def inspect(root, ident):
    try:
        return _inspect(root, ident)
    except (zipfile.BadZipFile, RuntimeError, KeyError, TypeError) as exc:
        raise KitError('Checkpoint incompleto, corrupto o con formato inválido.') from exc


def _inspect(root, ident):
    folder = checkpoint_path(root, ident)
    record = read_json(folder / 'checkpoint.json')
    if not isinstance(record, dict):
        raise KitError('Registro de checkpoint inválido.')
    checksum = record.get('record_sha256')
    unsigned = {k: v for k, v in record.items() if k != 'record_sha256'}
    if digest(unsigned) != checksum or record.get('format') != 'uasek.checkpoint' or record.get('format_version') != 1 or record.get('id') != ident:
        raise KitError('Metadatos de checkpoint alterados o incompatibles.')
    memory.validate_state(record['state'])
    snapshot = folder / 'sources.zip'
    if snapshot.stat().st_size > MAX_SNAPSHOT + 5_000_000:
        raise KitError('Archivo de checkpoint demasiado grande.')
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != record['snapshot_sha256']:
        raise KitError('Snapshot alterado.')
    with zipfile.ZipFile(snapshot) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(record['files']):
            raise KitError('Manifiesto de archivos no coincide.')
        if sum(item.file_size for item in archive.infolist()) > MAX_SNAPSHOT:
            raise KitError('Contenido descomprimido excede límite.')
        folded = set()
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or not path.parts or any(part.rstrip(' .') != part for part in path.parts):
                raise KitError('Ruta insegura en snapshot.')
            if any(re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I) for part in path.parts):
                raise KitError('Nombre reservado en snapshot.')
            if name.casefold() in folded:
                raise KitError('Colisión de rutas en snapshot.')
            folded.add(name.casefold())
            if is_sensitive(path) or hashlib.sha256(archive.read(name)).hexdigest() != record['files'][name]:
                raise KitError('Archivo sensible o checksum inválido en snapshot.')
    return record


def list_checkpoints(root):
    folder = safe_path(root, DIRECTORY)
    if not folder.exists():
        return []
    results = []
    for path in sorted(folder.iterdir()):
        if path.is_dir() and not path.is_symlink():
            record = inspect(root, path.name)
            results.append({k: record[k] for k in ('id', 'label', 'created_at', 'expected_outcome', 'tests_fresh_and_passing')})
    return results


def restore(root, ident, destination, dry_run=False):
    """Stage into a new directory only. Never reset Git or overwrite current code."""
    record = inspect(root, ident)
    target = Path(destination).resolve()
    root = Path(root).resolve()
    if target.exists() or target.is_relative_to(root):
        raise KitError('Recuperación requiere carpeta nueva fuera del proyecto actual.')
    if dry_run:
        return {'destination': str(target), 'checkpoint': ident, 'files': len(record['files']), 'dry_run': True}
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(checkpoint_path(root, ident) / 'sources.zip') as archive:
        for name in record['files']:
            path = safe_path(target, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(archive.read(name))
    # Canonical structured memory is also retained even if its source was omitted by redaction.
    memory.save(target, deepcopy(record['state']))
    write_json(safe_path(target, 'project-memory/RECOVERY.json'), {
        'checkpoint': ident, 'source_fingerprint': record['source_fingerprint'],
        'omitted': record['omitted'], 'tests_fresh_when_captured': record['tests_fresh_and_passing'],
        'next': 'Revisar diferencias y ejecutar pruebas de nuevo antes de integrar.'})
    return {'destination': str(target), 'checkpoint': ident, 'files': len(record['files']),
            'tests_must_be_rerun': True, 'dry_run': False}
