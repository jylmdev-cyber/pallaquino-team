"""Docs as Code: public allowlist, derived catalogs, drift and local build checks.

Never imports repository modules to discover Python API contracts, never executes
discovered scripts, and never deploys or calls Git. Only build invokes npm.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import quote, unquote, urlsplit

from .common import KitError, atomic_write, is_sensitive, redact, safe_path, state_lock

PORTAL = 'documentation/portal'
GENERATED = PORTAL + '/generated'
SITE = GENERATED + '/site'
MANIFEST = GENERATED + '/_manifest.json'
REPOSITORY = 'https://github.com/jylmdev-cyber/pallaquino-team'
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\((<[^>]+>|[^\s)]+)\)')
SECTIONS = [
    ('Introducción', '/introduction/overview'), ('Instalación', '/getting-started/install'),
    ('Arquitectura', '/architecture/overview'), ('Desarrollo', '/development/workflow'),
    ('Automatización', '/automation/overview'), ('Seguridad', '/security/overview'),
    ('Integraciones', '/integrations/providers'), ('Despliegue', '/deployment/pages'),
    ('API y CLI', '/api/overview'), ('Solución de problemas', '/troubleshooting/common'),
    ('Versiones', '/changelog/versions')]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def read(root, relative):
    path = safe_path(root, relative)
    if path.is_symlink() or not path.is_file() or is_sensitive(path) or path.stat().st_size > 2_000_000:
        raise KitError('Fuente documental no publicable: ' + relative)
    text = path.read_text(encoding='utf-8')
    if redact(text) != text:
        raise KitError('Posible secreto en fuente documental; revisar sin publicarlo: ' + relative)
    return text


def plain(markdown):
    return re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*(?:\n|$)', '', markdown)


def strip_frontmatter(text):
    return re.sub(r'\A---\s*\n.*?\n---\s*\n', '', text, count=1, flags=re.S)


def source_link(relative):
    return REPOSITORY + '/blob/main/' + quote(relative, safe='/')


def discover(root):
    """Only documented public inputs; no project memory, audits or credentials."""
    root = Path(root).resolve()
    sources = {'README.md', 'QUICKSTART.md', 'LICENSE', 'pyproject.toml',
               'configs/agents.json', 'configs/catalog.json'}
    for folder, pattern in [('docs', '*.md'), ('skills', 'SKILL.md'), ('agents', 'AGENT.md'),
                            ('templates/systems', 'SYSTEM.md'), ('tools', '*.py'),
                            ('scripts', '*.py'), ('uasek', '*.py'), ('workflows', '*.md')]:
        for path in safe_path(root, folder).rglob(pattern):
            relative = path.relative_to(root).as_posix()
            if relative.startswith('docs/quality/evidence/'):
                continue
            sources.add(relative)
    for relative in ['examples/platform/demo.py', 'kit.py', 'ai/adapters/README.md',
                     'documentation/PORTAL_MANUAL.md', 'documentation/ENGINE_DECISION.md']:
        if safe_path(root, relative).is_file():
            sources.add(relative)
    for path in safe_path(root, 'documentation/content').rglob('*.md'):
        sources.add(path.relative_to(root).as_posix())
    for relative in (PORTAL+'/package.json', PORTAL+'/package-lock.json', PORTAL+'/.vitepress/config.mjs'):
        if safe_path(root,relative).is_file():
            sources.add(relative)
    for folder in (PORTAL+'/.vitepress/theme',PORTAL+'/public'):
        for path in safe_path(root,folder).rglob('*'):
            if path.is_file() and path.suffix in {'.js','.mjs','.vue','.css','.svg'}:
                sources.add(path.relative_to(root).as_posix())
    return {relative: digest(read(root, relative).encode('utf-8')) for relative in sorted(sources)}


def inventory(root):
    agents=json.loads(read(root,'configs/agents.json'))
    catalog=json.loads(read(root,'configs/catalog.json'))
    if not isinstance(agents,dict) or not isinstance(catalog,list):
        raise KitError('Catálogos documentales inválidos.')
    seen=set()
    for entry in catalog:
        if not isinstance(entry,dict) or not isinstance(entry.get('id'),str) or not re.fullmatch(r'[a-z0-9-]+',entry['id']) or entry['id'] in seen:
            raise KitError('ID de referencia inválido o duplicado.')
        seen.add(entry['id'])
        if entry.get('path')!='templates/systems/'+entry['id']+'/SYSTEM.md':
            raise KitError('Ruta de referencia fuera del contrato público.')
    skills=[p.parent.name for p in safe_path(root,'skills').rglob('SKILL.md')]
    if len(skills)!=len(set(skills)):
        raise KitError('IDs de skills duplicados; no se sobrescribe una ficha.')
    missing=[]
    for path in safe_path(root,'agents').rglob('AGENT.md'):
        if path.parent.name not in agents:
            missing.append(path.relative_to(root).as_posix()+' no registrado en configs/agents.json')
    for ident in agents:
        if not safe_path(root,'agents/'+ident+'/AGENT.md').is_file():
            missing.append('agents/'+ident+'/AGENT.md ausente')
    known={entry['path'] for entry in catalog}
    for path in safe_path(root,'templates/systems').rglob('SYSTEM.md'):
        if path.relative_to(root).as_posix() not in known:
            missing.append(path.relative_to(root).as_posix()+' no registrado en configs/catalog.json')
    return missing


def mapping(root):
    result = {}
    for relative in discover(root):
        if relative.startswith(('docs/', 'workflows/')) and relative.endswith('.md'):
            result[relative] = 'generated/reference/' + relative
    for relative in ('README.md', 'QUICKSTART.md', 'LICENSE', 'ai/adapters/README.md',
                     'documentation/PORTAL_MANUAL.md', 'documentation/ENGINE_DECISION.md'):
        if safe_path(root, relative).is_file():
            result[relative] = 'generated/reference/' + relative + ('' if relative.endswith('.md') else '.md')
    for path in safe_path(root, 'documentation/content').rglob('*.md'):
        result[path.relative_to(root).as_posix()] = path.relative_to(safe_path(root, 'documentation/content')).as_posix()
    for path in safe_path(root, 'skills').rglob('SKILL.md'):
        result[path.relative_to(root).as_posix()] = 'generated/skills/' + path.parent.name + '.md'
    for entry in json.loads(read(root, 'configs/catalog.json')):
        result[entry['path']] = 'generated/examples/' + entry['id'] + '.md'
    return result


def rewrite(root, relative, text, routes):
    """Resolve links from original source location; don't rewrite code examples."""
    def replace(match):
        label, target = match[1], match[2].strip('<>')
        if target.startswith(('#', '//', '/generated/')) or urlsplit(target).scheme:
            return match[0]
        parsed = urlsplit(target)
        path = safe_path(root, str(Path(relative).parent / unquote(parsed.path)))
        if not path.exists():
            raise KitError('Enlace fuente roto: ' + relative + ' -> ' + target)
        destination = path.relative_to(root).as_posix()
        if destination.startswith(('.uasek/', 'project-memory/', 'docs/quality/evidence/')) or is_sensitive(path):
            return label + ' (referencia local no publicada)'
        if destination in routes:
            url = '/' + routes[destination].removesuffix('.md') + '.html'
        else:
            url = source_link(destination)
        return '[' + label + '](' + url + ('#' + parsed.fragment if parsed.fragment else '') + ')'
    pieces = re.split(r'(?m)(^```[^\n]*\n.*?^```[^\n]*(?:\n|$))', text, flags=re.S)
    return ''.join(piece if piece.startswith('```') else LINK.sub(replace, piece) for piece in pieces)


def note(relative):
    return '\n\n::: info Fuente mantenida en el repositorio\nEsta página se deriva de [' + relative + '](' + source_link(relative) + '). Edita la fuente y regenera el portal; no se mantiene una segunda copia manual.\n:::\n\n'


def bullets(values):
    return '\n'.join('- ' + str(value) for value in values) + '\n'


def expected(root):
    """Compute every output before writing; abort on invalid or sensitive input."""
    inventory(root)
    sources = discover(root)
    routes = mapping(root)
    version = tomllib.loads(read(root, 'pyproject.toml'))['project']['version']
    agents = json.loads(read(root, 'configs/agents.json'))
    catalog = json.loads(read(root, 'configs/catalog.json'))
    outputs = {}
    for relative, route in routes.items():
        text = read(root, relative)
        if relative.startswith('documentation/content/'):
            outputs[SITE + '/' + route] = text
        else:
            text = strip_frontmatter(text)
            if relative == 'LICENSE':
                text = '# Licencia MIT\n\n```text\n' + text + '\n```\n'
            if relative.endswith('SKILL.md'):
                name = route.split('/')[-1][:-3]
                compatible = [ident for ident, agent in agents.items() if name in agent.get('skills', [])]
                text += '\n## Agentes compatibles declarados\n\n' + (bullets(['[' + ident + '](/generated/agents/' + ident + '.html)' for ident in compatible]) if compatible else 'Sin asignación específica en configs/agents.json. Revisar el contrato antes de utilizarla.\n')
            text = rewrite(root, relative, text, routes)
            outputs[SITE + '/' + route] = text + note(relative)
    agent_links, skill_links, example_links = [], [], []
    for ident, agent in agents.items():
        if not re.fullmatch(r'[a-z0-9-]+', ident):
            raise KitError('ID de agente no portable.')
        text = '# ' + agent['role'] + '\n\n`' + ident + '` · Contrato de agente; no implica un modelo ejecutándose.\n'
        fields = [('Propósito', 'objectives'), ('Responsabilidades y capacidades', 'responsibilities'),
                  ('Herramientas permitidas', 'allowed_tools'), ('Entradas y dependencias', 'required_inputs'),
                  ('Salidas y entregables', 'deliverables'), ('Permisos y restricciones', 'restrictions'),
                  ('Criterios de aceptación', 'acceptance_criteria'), ('Escalamiento', 'escalation')]
        for title, field in fields:
            text += '\n## ' + title + '\n\n' + bullets(agent.get(field, []))
        text += '\n## Skills asociadas\n\n' + bullets(['[' + s + '](/generated/skills/' + s + '.html)' for s in agent.get('skills', [])])
        text += '\n## Comunicación y transferencia\n\n' + agent.get('communication', '') + '\n\n' + agent.get('handoff', '')
        text += '\n\n## Ejemplo de uso\n\nConsultar el contrato y preparar un encargo para una tarea existente:\n\n```console\npython kit.py agent show --name ' + ident + '\npython kit.py agent brief --task T0001\n```\n\nEl perfil de la tarea se establece al crearla. Ningún contrato concede permisos fuera de la política del proyecto.\n'
        outputs[SITE + '/generated/agents/' + ident + '.md'] = text + note('configs/agents.json')
        agent_links.append({'text': agent['role'], 'link': '/generated/agents/' + ident})
    for relative, route in routes.items():
        if relative.endswith('SKILL.md'):
            ident = Path(relative).parent.name
            skill_links.append({'text': ident, 'link': '/' + route[:-3]})
    for entry in catalog:
        example_links.append({'text': entry['name'], 'link': '/generated/examples/' + entry['id']})
    for category, links, explanation in [('agents', agent_links, 'Contratos de roles con sus límites y entregables.'),
                                         ('skills', skill_links, 'Instrucciones operativas versionadas por capacidad.'),
                                         ('examples', example_links, 'Referencias adaptables por industria; no son aplicaciones implementadas.')]:
        outputs[SITE + '/generated/' + category + '/index.md'] = '# ' + {'agents':'Agentes','skills':'Skills','examples':'Ejemplos por rubro'}[category] + '\n\n' + explanation + '\n\n' + bullets(['[' + item['text'] + '](' + item['link'] + '.html)' for item in links])
    # The trusted argparse parser is inspected, never execute discovered programs.
    from .cli import parser as kit_parser
    parser = kit_parser()
    cli_links = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, child in action.choices.items():
                outputs[SITE + '/generated/cli/' + name + '.md'] = '# CLI: ' + name + '\n\nReferencia generada del parser real; no ejecuta el comando.\n\n```text\n' + child.format_help() + '\n```\n\n[Flags globales y referencia CLI](index.html).\n'
                cli_links.append({'text': name, 'link': '/generated/cli/' + name})
    outputs[SITE + '/generated/cli/index.md'] = '# Referencia CLI\n\n```text\n' + parser.format_help() + '\n```\n\n## Comandos\n\n' + bullets(['[' + item['text'] + '](' + item['link'] + '.html)' for item in cli_links])
    script_links = []
    script_ids=set()
    for relative in sources:
        if not relative.endswith('.py') or not relative.startswith(('tools/', 'scripts/', 'examples/')):
            continue
        tree = ast.parse(read(root, relative))
        name = Path(relative).stem
        if name in script_ids:
            raise KitError('Scripts con el mismo nombre requieren rutas de ficha distintas: '+name)
        script_ids.add(name)
        title = ast.get_docstring(tree) or 'Script Python del proyecto.'
        args = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument':
                flags = [v.value for v in node.args if isinstance(v, ast.Constant) and isinstance(v.value, str)]
                help_value = next((k.value.value for k in node.keywords if k.arg == 'help' and isinstance(k.value, ast.Constant)), '')
                args.append('`' + ', '.join(flags) + '` — ' + str(help_value or 'Consultar --help para tipo, valor predeterminado y restricciones.'))
        body = '# Script: ' + name + '\n\n' + title + '\n\n## Ubicación y requisitos\n\n`' + relative + '` · Python 3.11+; ejecutar desde la raíz del checkout.\n\n## Ayuda y argumentos\n\n```console\npython ' + relative + ' --help\n```\n\n'
        wrapper = re.search(r"main\(global_args \+ \['([^']+)'\]", read(root, relative))
        if wrapper:
            body += 'Entrada de compatibilidad para [' + wrapper[1] + '](/generated/cli/' + wrapper[1] + '.html). Sus argumentos, ejemplos y controles son los del comando central.\n'
        else:
            body += bullets(args) if args else 'Consultar la ayuda CLI. El catálogo no ejecuta scripts descubiertos.\n'
        body += '\n## Uso, resultado y errores\n\nLa ayuda explica la operación. Para la demo: `--destination ../demo-eip --approve-demo`; para empaquetar: `--destination ../entrega.zip`. Un destino existente se rechaza cuando la operación requiere crear una carpeta o archivo nuevo. Revisar códigos de salida, permisos y rutas antes de ejecutar. Los wrappers devuelven el mismo JSON y códigos que la CLI central.\n'
        outputs[SITE + '/generated/scripts/' + name + '.md'] = body + note(relative)
        script_links.append({'text': name, 'link': '/generated/scripts/' + name})
    outputs[SITE + '/generated/scripts/index.md'] = '# Automatizaciones Python\n\nCatálogo generado sin ejecutar los scripts. Las opciones se obtienen del AST o del parser central de confianza.\n\n' + bullets(['[' + item['text'] + '](' + item['link'] + '.html)' for item in script_links])
    api_links = []
    for relative in sources:
        if not relative.startswith('uasek/') or not relative.endswith('.py'):
            continue
        tree = ast.parse(read(root, relative))
        module = relative[:-3].replace('/', '.')
        lines = ['# ' + module, ast.get_docstring(tree) or 'Módulo interno de la plataforma.',
                 '::: warning Contrato interno\nLa interfaz universal estable es la CLI. Estas firmas se extraen sin importar el módulo y pueden evolucionar con el software. No representan endpoints HTTP.\n:::']
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith('_'):
                lines.extend(['## ' + node.name, '```python\n' + node.name + '(' + ast.unparse(node.args) + ')\n```', ast.get_docstring(node) or 'Consultar la implementación y las pruebas enlazadas en el repositorio.'])
            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                lines.extend(['## ' + node.name, ast.get_docstring(node) or 'Clase interna.'])
        outputs[SITE + '/generated/api/' + module + '.md'] = '\n\n'.join(lines) + note(relative)
        api_links.append({'text': module, 'link': '/generated/api/' + module})
    outputs[SITE + '/generated/api/index.md'] = '# Módulos Python\n\nInventario estático. [Contrato público CLI](/api/overview.html).\n\n' + bullets(['[' + item['text'] + '](' + item['link'] + '.html)' for item in api_links])
    refs = [{'text': Path(relative).stem, 'link': '/' + route[:-3]} for relative, route in routes.items() if route.startswith('generated/reference/')]
    outputs[SITE + '/generated/reference/index.md'] = '# Documentación existente\n\nContenido reutilizado directamente desde sus fuentes. Los reportes anteriores conservan su versión y fecha; sus evidencias locales no se publican en este portal.\n\n' + bullets(['[' + r['text'] + '](' + r['link'] + '.html)' for r in refs])
    sidebar = [{'text':'Guías del proyecto','items':[{'text':name,'link':link} for name,link in SECTIONS]},
               {'text':'Catálogos','items':[
                   {'text':'Agentes','collapsed':True,'items':[{'text':'Catálogo','link':'/generated/agents/index'}]+agent_links},
                   {'text':'Skills','collapsed':True,'items':[{'text':'Catálogo','link':'/generated/skills/index'}]+skill_links},
                   {'text':'Ejemplos por rubro','collapsed':True,'items':[{'text':'Catálogo','link':'/generated/examples/index'}]+example_links}]},
               {'text':'Referencias','items':[{'text':'CLI','link':'/generated/cli/index'},
                    {'text':'Scripts Python','link':'/generated/scripts/index'}, {'text':'Módulos internos','link':'/generated/api/index'},
                    {'text':'Documentación de origen','link':'/generated/reference/index'},
                    {'text':'Administrar el portal','link':'/generated/reference/documentation/PORTAL_MANUAL'}]}]
    meta = {'project':'PALLAQUINO TEAM','version':version,'portal_version':1,'agents':len(agent_links),
            'skills':len(skill_links),'examples':len(example_links),'scripts':len(script_links),'modules':len(api_links),'sidebar':sidebar}
    outputs[PORTAL + '/.vitepress/generated.json'] = json_text(meta)
    # Content is reviewed project documentation, but fail closed on secret-like bytes.
    for relative, text in outputs.items():
        if redact(text) != text:
            raise KitError('Salida con posible secreto; revisar fuente antes de generar: ' + relative)
    return outputs, sources, meta


def previous(root):
    path = safe_path(root, MANIFEST)
    if not path.exists():
        return {'schema_version':1,'sources':{},'outputs':{}}
    value = json.loads(path.read_text(encoding='utf-8'))
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1 or not isinstance(value.get('outputs'),dict) or not isinstance(value.get('sources'),dict):
        raise KitError('Manifiesto documental incompatible.')
    for relative,checksum in value['outputs'].items():
        if not isinstance(relative,str) or not relative.startswith(PORTAL+'/') or not isinstance(checksum,str) or not re.fullmatch(r'[a-f0-9]{64}',checksum):
            raise KitError('Salida de manifiesto fuera de contrato.')
        safe_path(root,relative)
    return value


def status(root):
    _, sources, meta = expected(root)
    old = previous(root)
    changed = sorted(k for k,v in sources.items() if old.get('sources',{}).get(k) != v)
    removed = sorted(set(old.get('sources',{}))-set(sources))
    edited = [k for k,v in old['outputs'].items() if not safe_path(root,k).is_file() or digest(safe_path(root,k).read_bytes()) != v]
    return {'schema_version':1,'project':meta['project'],'software_version':meta['version'],
            'stale':bool(changed or removed or edited),'changed_sources':changed,'removed_sources':removed,
            'missing_or_edited_outputs':edited,'catalogs':{k:meta[k] for k in ('agents','skills','examples','scripts','modules')},
            'sources':len(sources),'publication':'prepared-only; no deployment performed'}


def generate(root):
    root = Path(root).resolve()
    with state_lock(root):
        outputs, sources, meta = expected(root)
        old = previous(root)
        for relative, checksum in old['outputs'].items():
            path = safe_path(root,relative)
            if path.exists() and digest(path.read_bytes()) != checksum:
                raise KitError('Salida generada editada; conservar/revisar manualmente antes de regenerar: ' + relative)
        for relative in outputs:
            path = safe_path(root,relative)
            if path.exists() and relative not in old['outputs']:
                raise KitError('No se sobrescribe archivo manual sin propietario de generación: ' + relative)
        for path in safe_path(root,GENERATED).rglob('*'):
            if path.is_file() and path.relative_to(root).as_posix() not in set(old['outputs']) | {MANIFEST}:
                raise KitError('Archivo manual inesperado en carpeta generada: ' + str(path.name))
        for relative, text in outputs.items():
            atomic_write(safe_path(root,relative),text)
        for relative in set(old['outputs'])-set(outputs):
            if not relative.startswith(PORTAL+'/') or (not relative.endswith('.md') and not relative.startswith(GENERATED+'/')):
                raise KitError('Manifiesto intenta retirar archivo fuera de su alcance.')
            safe_path(root,relative).unlink(missing_ok=True)
        manifest = {'schema_version':1,'sources':sources,'outputs':{p:digest(t.encode('utf-8')) for p,t in outputs.items()}}
        atomic_write(safe_path(root,MANIFEST),json_text(manifest))
    return {'generated_files':len(outputs),'sources':len(sources),'catalogs':{k:meta[k] for k in ('agents','skills','examples','scripts','modules')},'manual_sources_overwritten':False}


def scan(root):
    report = status(root)
    outputs, _, _ = expected(root)
    report['documentation_pages'] = sum(k.endswith('.md') for k in outputs)
    report['unregistered_or_missing_contracts']=inventory(root)
    report['coverage'] = 'Todos los agentes, skills, plantillas de catálogo, scripts y módulos detectados tienen una ficha derivada; no mide completitud semántica.'
    report['potentially_affected'] = {
        'catalogs':any(p.startswith(('skills/','agents/','configs/')) for p in report['changed_sources']),
        'cli_and_api':any(p.startswith(('uasek/','tools/')) for p in report['changed_sources']),
        'architecture_review':any(p.startswith(('uasek/','configs/')) for p in report['changed_sources'])}
    return report


def route_file(root, target, source):
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith('//'):
        if parsed.scheme and parsed.scheme not in {'http','https','mailto'}:
            raise KitError('Esquema de enlace no permitido: ' + parsed.scheme)
        return None
    relative = unquote(parsed.path)
    if relative.startswith('/'):
        path = safe_path(root, SITE + '/' + relative.lstrip('/'))
    else:
        path = safe_path(root, str(Path(source).parent / relative)) if relative else safe_path(root,source)
    if path.suffix == '.html':
        path = path.with_suffix('.md')
    elif not path.suffix:
        path = path.with_suffix('.md')
    return path


def validate(root):
    report = status(root)
    if report['stale']:
        raise KitError('Documentación desactualizada: ejecutar generate y revisar scan/status.')
    if inventory(root):
        raise KitError('Componentes sin contrato o registro documental: '+'; '.join(inventory(root)))
    owned=set(previous(root)['outputs'])
    for path in safe_path(root,PORTAL).rglob('*.md'):
        relative=path.relative_to(root).as_posix()
        if any(part in {'node_modules','.vitepress'} for part in path.relative_to(safe_path(root,PORTAL)).parts):
            continue
        if relative not in owned:
            raise KitError('Markdown sin fuente pública autorizada dentro del portal: '+relative)
    for path in safe_path(root,PORTAL+'/public').rglob('*'):
        if not path.is_file():
            continue
        if is_sensitive(path) or (path.name!='CNAME' and path.suffix not in {'.svg','.png','.jpg','.jpeg','.webp','.ico','.woff2'}):
            raise KitError('Recurso estático no permitido: '+path.name)
        if path.suffix=='.svg' or path.name=='CNAME':
            read(root,path.relative_to(root).as_posix())
    count = 0
    for relative in previous(root)['outputs']:
        if not relative.endswith('.md'):
            continue
        text = plain(read(root,relative))
        for match in LINK.finditer(text):
            path = route_file(root,match[2].strip('<>'),relative)
            if path is not None and not path.is_file():
                raise KitError('Enlace interno roto: ' + relative + ' -> ' + match[2])
            count += 1
        for link in re.findall(r'(?m)^\s+link:\s*[\'\"]?(/[^\s\'\"]+)',text):
            path = route_file(root,link,relative)
            if path is not None and not path.is_file():
                raise KitError('Tarjeta o acción sin destino: ' + relative + ' -> ' + link)
    meta=json.loads(read(root,PORTAL+'/.vitepress/generated.json'))
    def nav(items):
        for item in items:
            if 'link' in item and not route_file(root,item['link'],SITE+'/index.md').is_file():
                raise KitError('Navegación sin destino: '+item['link'])
            nav(item.get('items',[]))
    nav(meta['sidebar'])
    return {'valid':True,'links_checked':count,'pages':sum(p.endswith('.md') for p in previous(root)['outputs']),
            'scope':'Rutas fuente, navegación y tarjetas; build comprueba renderizado y post-build verifica también anclas y recursos.'}


class HtmlReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if 'id' in data:
            self.ids.add(data['id'])
        for name in ('href','src'):
            if name in data:
                self.links.append(data[name])


def validate_build(root, base=None):
    """Check all built local href/src targets and fragments under a Pages base."""
    directory = safe_path(root,PORTAL+'/.vitepress/dist')
    repository=os.environ.get('GITHUB_REPOSITORY') or 'jylmdev-cyber/pallaquino-team'
    if not re.fullmatch(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+',repository):
        raise KitError('GITHUB_REPOSITORY inválido.')
    owner,repo=repository.split('/')
    default_base='/' if repo.lower()==owner.lower()+'.github.io' else '/'+repo+'/'
    base = base or os.environ.get('DOCS_BASE') or default_base
    if not re.fullmatch(r'/(?:[a-zA-Z0-9_.-]+/)*',base):
        raise KitError('DOCS_BASE inválida.')
    parsed = {}
    for path in directory.rglob('*.html'):
        parser = HtmlReferences()
        parser.feed(path.read_text(encoding='utf-8'))
        parsed[path.resolve()] = parser
    if not parsed or not (directory/'index.html').is_file():
        raise KitError('Build inexistente o incompleto.')
    links = 0
    for path, parser in parsed.items():
        for target in parser.links:
            url=urlsplit(target)
            if url.scheme or target.startswith('//'):
                if url.scheme not in {'http','https','mailto','data'}:
                    raise KitError('Enlace ejecutable o esquema no permitido en build.')
                continue
            relative=unquote(url.path)
            if relative.startswith('/'):
                if not relative.startswith(base):
                    raise KitError('Recurso ignora base de Pages: '+target)
                candidate=safe_path(directory,relative[len(base):])
            else:
                candidate=safe_path(directory,str(path.parent/relative)) if relative else path
            if candidate.is_dir():
                candidate=candidate/'index.html'
            if not candidate.is_file():
                raise KitError('Recurso o página no existe en build: '+str(path.relative_to(directory))+' -> '+target)
            if url.fragment and candidate.suffix=='.html' and unquote(url.fragment) not in parsed[candidate.resolve()].ids:
                raise KitError('Ancla inexistente: '+str(path.relative_to(directory))+' -> '+target)
            links+=1
    # Public builds must not accidentally contain private runtime sources.
    forbidden={'.env','state.json','audit.jsonl','approvals','credentials.json','secrets.json'}
    if any(p.name in forbidden for p in directory.rglob('*')):
        raise KitError('Build contiene archivo privado no permitido.')
    return {'valid':True,'html_pages':len(parsed),'local_references_checked':links,'base':base,
            'private_sources_included':False,'deployed':False}


def build(root):
    generate(root)
    validate(root)
    executable=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not executable or not safe_path(root,PORTAL+'/node_modules/vitepress').is_dir():
        raise KitError('Instalar Node 24.22 y ejecutar npm ci --ignore-scripts en documentation/portal.')
    result=subprocess.run([executable,'run','build'],cwd=safe_path(root,PORTAL),capture_output=True,text=True,encoding='utf-8',timeout=600)
    if result.returncode:
        raise KitError('Build falló: '+redact((result.stdout+result.stderr)[-7000:]))
    return validate_build(root)


def prepare_deploy(root):
    report=build(root)
    atomic_write(safe_path(root,PORTAL+'/.vitepress/dist/.nojekyll'),'')
    report.update(artifact=PORTAL+'/.vitepress/dist',publication='Preparado, sin cambios remotos. Habilitación UDP_PAGES_ENABLED y autorización de publicación pendientes.')
    return report


def permission_scope(root, args):
    """Reuse EIP's local policy; previewing a resource never executes npm."""
    from .eip import store
    if not store.location(root,'state.json').exists():
        return None
    action='execute' if args.command in {'build','prepare-deploy'} else 'memory.write' if args.command=='generate' or args.report else None
    if action is None:
        return None
    from .context_format import digest as context_digest
    from .operations import source_fingerprint
    return {'permission':action,'resource':'udp:'+context_digest({'command':args.command,
        'root':str(Path(root).resolve()),'report':args.report,'base':args.base,
        'source_fingerprint':source_fingerprint(root),'public_sources':discover(root),
        'build_environment':{name:os.environ.get(name,'') for name in ('DOCS_BASE','DOCS_ORIGIN','GITHUB_REPOSITORY')}})}


def main(argv=None):
    if sys.platform=='win32':
        for stream in (sys.stdout,sys.stderr):
            if hasattr(stream,'reconfigure'):
                stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Portal UDP: generación reproducible, cobertura, validación y build local; nunca publica.')
    parser.add_argument('command',choices=['scan','generate','validate','build','status','prepare-deploy','validate-build'])
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--report',help='Informe JSON nuevo, relativo a la raíz; no sobrescribe archivos.')
    parser.add_argument('--base',help='Base para validate-build, por ejemplo /pallaquino-team/ o /.')
    parser.add_argument('--policy-preview',action='store_true',help='Mostrar permiso/recurso sin escribir ni ejecutar.')
    parser.add_argument('--platform-approval',help='Aprobación EIP acotada al comando y fuentes actuales.')
    args=parser.parse_args(argv)
    try:
        root=Path(args.root).resolve()
        scope=permission_scope(root,args)
        if args.policy_preview:
            print(json_text(scope or {'permission':'read','resource':None}),end='')
            return 0
        from .eip.cli import authorize_legacy
        authorize_legacy(root,scope,args.platform_approval)
        functions={'scan':scan,'generate':generate,'validate':validate,'build':build,'status':status,'prepare-deploy':prepare_deploy}
        report=validate_build(root,args.base) if args.command=='validate-build' else functions[args.command](root)
        serialized=json_text(report)
        if args.report:
            path=safe_path(root,args.report)
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x',encoding='utf-8') as stream:
                stream.write(serialized)
        print(serialized,end='')
        return 0
    except (KitError,OSError,ValueError,SyntaxError,subprocess.TimeoutExpired) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
