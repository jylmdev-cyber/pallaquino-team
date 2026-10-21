"""Capability/cost/latency/privacy selection from reviewed declared model metadata."""
import math

from . import store
from ..common import KitError, read_json


def validate_models(value):
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value.get('schema_version') != 1 or not isinstance(value.get('models'), list):
        raise KitError('Catálogo de modelos incompatible.')
    ids = set()
    for model in value['models']:
        required = {'id', 'provider', 'model', 'adapter', 'capabilities', 'complexity', 'estimated_cost_units',
                    'estimated_latency_ms', 'available', 'privacy', 'tools', 'observed_at', 'source'}
        if not isinstance(model, dict) or set(model) != required:
            raise KitError('Modelo requiere capacidades, procedencia y estimaciones declaradas.')
        if any(not isinstance(model[key], str) or not model[key] for key in ('id', 'provider', 'model', 'adapter', 'observed_at', 'source')):
            raise KitError('Identidad de modelo inválida.')
        if model['id'] in ids or model['privacy'] not in {'local', 'remote'} or model['adapter'] not in {'manual', 'ollama'}:
            raise KitError('ID, privacidad o adaptador inválido.')
        ids.add(model['id'])
        if type(model['available']) is not bool or type(model['tools']) is not bool or type(model['complexity']) is not int or not 1 <= model['complexity'] <= 5:
            raise KitError('Disponibilidad, herramientas o complejidad inválidas.')
        if not isinstance(model['capabilities'], list) or any(not isinstance(v, str) for v in model['capabilities']):
            raise KitError('Capacidades inválidas.')
        for key in ('estimated_cost_units', 'estimated_latency_ms'):
            if type(model[key]) not in (int, float) or not math.isfinite(model[key]) or model[key] < 0:
                raise KitError('Estimación de modelo inválida.')


def select(root, requirements):
    catalog = read_json(store.location(root, 'models.json'))
    validate_models(catalog)
    capabilities = requirements.get('capabilities', [])
    privacy = requirements.get('privacy', 'local')
    complexity = requirements.get('complexity', 1)
    maximum = requirements.get('max_cost_units', 100)
    latency = requirements.get('max_latency_ms', 60000)
    if not isinstance(capabilities, list) or any(not isinstance(v, str) for v in capabilities) or privacy not in {'local', 'remote', 'any'} or type(complexity) is not int or not 1 <= complexity <= 5:
        raise KitError('Requisitos de modelo inválidos.')
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (maximum, latency)):
        raise KitError('Presupuesto/latencia inválidos.')
    candidates, rejected = [], []
    for model in catalog['models']:
        reasons = []
        if not model['available']:
            reasons.append('unavailable')
        if not set(capabilities) <= set(model['capabilities']):
            reasons.append('capabilities')
        if model['complexity'] < complexity:
            reasons.append('complexity')
        if privacy != 'any' and model['privacy'] != privacy:
            reasons.append('privacy')
        if requirements.get('tools') and not model['tools']:
            reasons.append('tools')
        if model['estimated_cost_units'] > maximum or model['estimated_latency_ms'] > latency:
            reasons.append('budget-or-latency')
        if reasons:
            rejected.append({'id': model['id'], 'reasons': reasons})
        else:
            candidates.append(model)
    if not candidates:
        raise KitError('Ningún modelo declarado cumple capacidades, presupuesto, disponibilidad y privacidad.')
    candidates.sort(key=lambda m: (m['estimated_cost_units'], m['estimated_latency_ms'], m['id']))
    return {'selected': candidates[0], 'alternatives': [m['id'] for m in candidates[1:]], 'rejected': rejected,
            'limits': 'Estimaciones declaradas con procedencia; no son precios en vivo ni medición garantizada. Selección no implica invocación.'}
