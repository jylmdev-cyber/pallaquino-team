"""Shared I/O, boundaries and redaction. No third-party runtime dependencies."""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request

KIT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = KIT_ROOT if (KIT_ROOT / 'configs/agents.json').exists() else Path(__file__).parent / 'resources'
IGNORED = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.uasek',
           'dist', 'build', 'backups', '.idea', '.pytest_cache'}
SENSITIVE = {'.env', '.npmrc', '.pypirc', 'credentials.json', 'secrets.json',
             'id_rsa', 'id_ed25519', '.netrc'}
SECRET_PATTERNS = [
    ('private-key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ('provider-token', re.compile(r'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b')),
    ('credential-assignment', re.compile(r'''(?im)\b(?:api[_-]?key|access[_-]?token|password|secret|authorization)\b["']?\s*[:=]\s*["']?([^\s"',;}{]{8,})''')),
    ('credential-url', re.compile(r'(?i)https?://[^\s/:]+:[^\s/@]+@[^\s]+')),
]


class KitError(Exception):
    """Expected, actionable CLI failure."""


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def redact(text):
    text = re.sub(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', '[REDACTED PRIVATE KEY]', text)
    for rule, pattern in SECRET_PATTERNS:
        if rule == 'credential-assignment':
            text = pattern.sub(lambda m: m[0][:m.start(1)-m.start()] + '[REDACTED]', text)
        else:
            text = pattern.sub('[REDACTED]', text)
    # Also remove values of credential-shaped environment variables in this process.
    for key, value in os.environ.items():
        if len(value) >= 8 and re.search(r'(?:TOKEN|SECRET|PASSWORD|API_KEY)', key, re.I):
            text = text.replace(value, '[REDACTED]')
    return text


def redact_data(value):
    """Redact before serializing so untrusted keys cannot corrupt JSON output."""
    if isinstance(value, dict):
        return {redact(str(k)): ('[REDACTED]' if re.fullmatch(r'(?:api[_-]?key|access[_-]?token|password|secret|authorization)', str(k), re.I)
                               else redact_data(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_data(v) for v in value]
    return redact(value) if isinstance(value, str) else value


def safe_path(root, relative):
    root = Path(root).resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise KitError('Ruta fuera del proyecto: ' + str(relative))
    return target


def read_json(path, default=None):
    if not Path(path).exists():
        if default is not None:
            return default
        raise KitError('No existe: ' + str(path))
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.uasek-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, data):
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


@contextlib.contextmanager
def state_lock(root):
    """Fail closed on simultaneous mutations; never silently lose task updates."""
    folder = safe_path(root, '.uasek')
    folder.mkdir(exist_ok=True)
    lock = folder / 'state.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise KitError('Memoria ocupada. Si hubo una interrupción, compruebe procesos antes de retirar .uasek/state.lock.') from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def files(root):
    """Bounded walker; never follows symlinks or Windows junctions."""
    root = Path(root).resolve()
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not d.endswith('.egg-info')
                         and not Path(base, d).is_symlink()
                         and not getattr(Path(base, d), 'is_junction', lambda: False)())
        for name in sorted(names):
            path = Path(base, name)
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                continue
            yield path


def is_sensitive(path):
    name = Path(path).name.lower()
    return (name in SENSITIVE or (name.startswith('.env') and name != '.env.example')
            or Path(name).suffix in {'.pem', '.key', '.p12', '.pfx', '.keystore'})


def run(argv, cwd, timeout=60):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout, shell=False)
    return {'command': argv, 'returncode': result.returncode,
            'stdout': redact(result.stdout[-60000:]), 'stderr': redact(result.stderr[-10000:])}


def http_json(url, data=None, timeout=15):
    payload = None if data is None else json.dumps(data).encode('utf-8')
    request = urllib.request.Request(url, data=payload, headers={
        'User-Agent': 'UASEK/1.0', 'Accept': 'application/json',
        'Content-Type': 'application/json'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise KitError('Redirección HTTP rechazada; verifique el endpoint explícito.')

    with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise KitError('Respuesta HTTP supera 5 MB.')
        return json.loads(raw)


def event(root, command, outcome):
    log = safe_path(root, '.uasek/events.jsonl')
    log.parent.mkdir(exist_ok=True)
    with log.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'at': now(), 'command': command, 'outcome': outcome}, ensure_ascii=False) + '\n')
