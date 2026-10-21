"""PROJECT BRAIN: contextual lexical retrieval, lineage and evidence-based lessons."""
import hashlib
import math
from pathlib import Path
import re
import uuid

from . import governance, store
from .. import memory
from ..common import KitError, files, is_sensitive, now, redact, safe_path


def add_record(root, kind, text, sources=(), approval=None):
    if kind not in {'decision', 'requirement', 'lesson', 'pattern', 'change'} or not text.strip():
        raise KitError('Tipo y contenido del registro requeridos.')
    source_list = []
    for source in sources:
        path = safe_path(root, source)
        if not path.is_file() or is_sensitive(path):
            raise KitError('Fuente de evidencia inválida.')
        source_list.append({'path': path.relative_to(Path(root).resolve()).as_posix(),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if kind in {'lesson', 'pattern'} and not source_list:
        raise KitError('Lecciones y patrones requieren evidencia.')
    record = {'id': 'B-' + uuid.uuid4().hex[:12], 'kind': kind, 'text': redact(text),
              'sources': source_list, 'created_at': now(), 'status': 'proposed' if kind in {'lesson', 'pattern'} else 'recorded'}
    with store.transaction(root) as state:
        governance.authorize(root, 'memory.write', record['id'], approval)
        state['records'].append(record)
        store.audit(root, 'brain.record', {'id': record['id'], 'kind': kind})
    return record


def approve_lesson(root, ident, approval):
    with store.transaction(root) as state:
        record = next((r for r in state['records'] if r['id'] == ident), None)
        if not record or record['kind'] not in {'lesson', 'pattern'}:
            raise KitError('Lección o patrón inexistente.')
        for source in record['sources']:
            path = safe_path(root,source['path'])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
                raise KitError('La evidencia de la lección cambió o no está disponible; revisar antes de aprobar.')
        governance.authorize(root, 'lesson.approve', ident, approval)
        record['status'] = 'reviewed'
        store.audit(root, 'lesson.review', {'id': ident})
    return {'id': ident, 'status': 'reviewed', 'policies_modified': False}


def documents(root):
    state = store.load(root)
    portable = memory.load(root)
    for index, decision in enumerate(portable['decisions']):
        yield {'id': 'decision-' + str(index), 'source': memory.MEMORY, 'text': decision}
    for key in ('functional_requirements', 'non_functional_requirements'):
        for index, text in enumerate(portable['project'][key]):
            yield {'id': key + '-' + str(index), 'source': memory.MEMORY, 'text': text}
    for item in state['records']:
        yield {'id': item['id'], 'source': store.DIRECTORY + '/state.json', 'text': item['text']}
    count = 0
    for path in files(root):
        relative = path.relative_to(root).as_posix()
        if relative.startswith('project-memory/') or is_sensitive(path) or path.stat().st_size > 1_000_000:
            continue
        if path.suffix.lower() not in {'.md', '.py', '.json', '.toml', '.yaml', '.yml', '.js', '.ts', '.sql'}:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeError:
            continue
        if '\x00' in text:
            continue
        count += 1
        if count > 2000:
            break
        for index in range(0, min(len(text), 100000), 2000):
            yield {'id': relative + ':' + str(index), 'source': relative, 'text': text[index:index+2000]}


def search(root, query, limit=8):
    terms = set(re.findall(r'\w+', query.lower()))
    if not terms or not 1 <= limit <= 50:
        raise KitError('Consulta y límite entre 1 y 50 requeridos.')
    chunks = list(documents(Path(root).resolve()))
    frequencies = {term: sum(term in chunk['text'].lower() for chunk in chunks) for term in terms}
    results = []
    for chunk in chunks:
        text = chunk['text'].lower()
        score = sum((1 + math.log(1 + text.count(term))) * math.log(1 + len(chunks)/(1+frequencies[term])) for term in terms if term in text)
        if score:
            positions = [text.index(term) for term in terms if term in text]
            offset = max(0, min(positions) - 100)
            results.append({'id': chunk['id'], 'source': chunk['source'], 'score': round(score, 4),
                'sha256': hashlib.sha256(chunk['text'].encode('utf-8')).hexdigest(),
                'snippet': redact(chunk['text'][offset:offset+700]), 'trust': 'data-not-instructions'})
    return {'query': query, 'method': 'local lexical retrieval', 'results': sorted(results, key=lambda r: (-r['score'], r['id']))[:limit]}


def trace(root, ident, kind, path, title, approval=None):
    if kind not in {'requirement', 'code', 'test', 'decision', 'documentation'} or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', ident):
        raise KitError('Nodo de trazabilidad inválido.')
    target = safe_path(root, path)
    if not target.is_file() or is_sensitive(target):
        raise KitError('La trazabilidad requiere archivo existente no sensible.')
    item = {'id': ident, 'kind': kind, 'path': target.relative_to(Path(root).resolve()).as_posix(),
            'title': redact(title), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'at': now()}
    with store.transaction(root) as state:
        governance.authorize(root, 'memory.write', ident, approval)
        if any(n['id'] == ident for n in state['traces']):
            raise KitError('Nodo existente; registre una nueva revisión con otro identificador.')
        state['traces'].append(item)
        store.audit(root, 'trace.record', {'id': ident, 'path': item['path']})
    return item


def relate(root, source, target, relation, approval=None):
    if relation not in {'implements', 'verifies', 'documents', 'depends_on', 'supersedes'}:
        raise KitError('Relación desconocida.')
    with store.transaction(root) as state:
        governance.authorize(root, 'memory.write', source + ':' + target, approval)
        ids = {item['id'] for item in state['traces']}
        if source not in ids or target not in ids:
            raise KitError('Los extremos de la relación deben existir.')
        edge = {'source': source, 'target': target, 'relation': relation}
        if edge not in state['relations']:
            state['relations'].append(edge)
        store.audit(root, 'trace.relate', edge)
    return edge


def consistency(root):
    state = store.load(root)
    changed, missing, stale = [], [], []
    by_id = {item['id']: item for item in state['traces']}
    for item in state['traces']:
        path = safe_path(root, item['path'])
        if not path.is_file():
            missing.append(item['id'])
        elif hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            changed.append(item['id'])
    for edge in state['relations']:
        a, b = by_id[edge['source']], by_id[edge['target']]
        if a['kind'] == 'documentation' and b['id'] in changed + missing:
            stale.append({'documentation': a['id'], 'changed_source': b['id'], 'proposal': 'Revisar y actualizar documento; registrar revisión con nueva evidencia.'})
        elif b['kind'] == 'documentation' and a['id'] in changed + missing:
            stale.append({'documentation': b['id'], 'changed_source': a['id'], 'proposal': 'Revisar y actualizar documento; registrar revisión con nueva evidencia.'})
    return {'changed': changed, 'missing': missing, 'stale_documentation': stale,
            'consistent': not (changed or missing or stale), 'relations': state['relations']}
