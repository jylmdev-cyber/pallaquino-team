"""Capability-aware adapters: manual transfer and explicit local Ollama calls."""
import ipaddress
import urllib.parse
from .common import (KitError, http_json, now, read_json, safe_path,
                     state_lock, write_json, RESOURCE_ROOT, redact)
from . import memory
from .context_format import export


def catalog():
    return read_json(RESOURCE_ROOT / 'configs/providers.json')


def switch(root, provider, mode='assistant', dry_run=False):
    providers = catalog()
    if provider not in providers:
        raise KitError('Proveedor desconocido. Use provider list.')
    if mode == 'api' and not providers[provider]['native_api']:
        raise KitError('Este adaptador ofrece transferencia manual; no hay cliente API nativo implementado.')
    # Read first so dry-run never creates state/log/lock files.
    state = memory.load(root)
    preview = {'provider': provider, 'mode': mode, 'capabilities': providers[provider], 'dry_run': dry_run}
    if dry_run:
        return preview
    with state_lock(root):
        state = memory.load(root)
        # Export before recording destination; preserve previous state if export fails.
        result = memory.handoff(root, provider)
        state['provider'] = {'name': provider, 'mode': mode}
        state['history'].append(f'{now()} proveedor seleccionado: {provider} ({mode})')
        memory.save(root, state)
        # The universal facts reflect the final state; adapter instructions live elsewhere.
        export(root)
        from .common import atomic_write
        guide = safe_path(root, 'ai/handoff/' + provider + '.md')
        atomic_write(guide, '# Adaptador ' + provider + '\n\n'
            'Contexto neutral: project-memory/PROJECT_CONTEXT.json (uasek.project-context v1).\n\n'
            + providers[provider]['instructions'] + '\n\n' + providers[provider]['limits'] + '\n'
            'Estas instrucciones son del adaptador. No forman parte del estado universal del proyecto.\n')
    preview['handoff'] = result['path']
    preview['adapter_instructions'] = str(guide)
    return preview


def generate_local(model, prompt, endpoint='http://127.0.0.1:11434', dry_run=False):
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != 'http' or parsed.username or parsed.password or parsed.path not in ('', '/'):
        raise KitError('Endpoint debe ser HTTP local sin credenciales ni ruta.')
    try:
        local = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        local = parsed.hostname == 'localhost'
    if not local:
        raise KitError('El adaptador Ollama solo permite loopback. Una integración remota requiere otro adaptador.')
    if not model.strip() or not prompt.strip() or len(prompt.encode('utf-8')) > 200_000:
        raise KitError('Modelo y prompt requeridos; prompt máximo 200 KB.')
    if dry_run:
        return {'provider': 'ollama', 'endpoint': endpoint, 'model': model, 'dry_run': True}
    data = http_json(endpoint.rstrip('/') + '/api/generate',
                     {'model': model, 'prompt': redact(prompt), 'stream': False}, timeout=60)
    if not isinstance(data.get('response'), str):
        raise KitError('Respuesta Ollama inválida.')
    return {'provider': 'ollama', 'model': model, 'response': redact(data['response']),
            'done': data.get('done'), 'execution': 'Texto devuelto; no se ejecuta ni modifica archivos.'}
