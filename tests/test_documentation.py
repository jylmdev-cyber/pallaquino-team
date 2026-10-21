"""Portal integrity and public-boundary checks without Node or network."""
import json
from pathlib import Path
import tempfile
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from uasek import documentation as docs, operations, memory
from uasek.common import KitError


class Documentation(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.root=Path(self.temporary.name).resolve()
        self.put('README.md','# Proyecto\n\n[Guía](docs/guide.md)\n')
        self.put('QUICKSTART.md','# Inicio\n')
        self.put('LICENSE','MIT License\n')
        self.put('pyproject.toml','[project]\nversion="2.0.0"\n')
        self.put('docs/guide.md','# Guía\n\n[Inicio](../README.md)\n')
        self.put('configs/agents.json',json.dumps({'developer':{'role':'Developer','objectives':['Implementar'],
            'skills':['sample'],'responsibilities':['Revisar'],'allowed_tools':['CLI'],
            'required_inputs':['Requisito'],'deliverables':['Código'],'restrictions':['Permisos'],
            'acceptance_criteria':['Pruebas'],'escalation':['Bloqueo'],'communication':'JSON','handoff':'Contexto'}}))
        self.put('configs/catalog.json',json.dumps([{'id':'sales','name':'Ventas','industry':'retail','path':'templates/systems/sales/SYSTEM.md'}]))
        self.put('templates/systems/sales/SYSTEM.md','# Ventas\n\nReferencia adaptable.\n')
        self.put('agents/developer/AGENT.md','# Developer\n')
        self.put('skills/ai/sample/SKILL.md','---\nname: sample\ndescription: Ejemplo\n---\n# Sample\n\n## Procedimiento\nRevisar.\n')
        self.put('uasek/example.py','"""Módulo estático."""\nraise RuntimeError("No importar")\ndef add(a,b=1):\n    return a+b\n')
        self.put('tools/example.py','"""Ejemplo de script."""\nraise RuntimeError("No ejecutar")\n')
        self.put('documentation/PORTAL_MANUAL.md','# Manual\n')
        self.put('documentation/content/index.md','# Portal\n')
        for _,route in docs.SECTIONS:
            self.put('documentation/content'+route+'.md','# Sección\n')

    def tearDown(self):
        self.temporary.cleanup()

    def put(self,relative,text):
        path=self.root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf-8')
        return path

    def test_generated_catalogs_derive_from_sources_without_executing_discovered_code(self):
        result=docs.generate(self.root)
        self.assertEqual(result['catalogs']['agents'],1)
        self.assertEqual(result['catalogs']['skills'],1)
        self.assertEqual(result['catalogs']['examples'],1)
        self.assertTrue(docs.validate(self.root)['valid'])
        page=(self.root/docs.SITE/'generated/api/uasek.example.md').read_text(encoding='utf-8')
        self.assertIn('add(a, b=1)',page)
        self.assertIn('developer.html',(self.root/docs.SITE/'generated/skills/sample.md').read_text(encoding='utf-8'))

    def test_generation_is_idempotent_and_source_drift_names_affected_components(self):
        docs.generate(self.root)
        first=(self.root/docs.MANIFEST).read_bytes()
        docs.generate(self.root)
        self.assertEqual(first,(self.root/docs.MANIFEST).read_bytes())
        self.put('uasek/example.py','def new_contract(value):\n    return value\n')
        report=docs.scan(self.root)
        self.assertTrue(report['stale'])
        self.assertIn('uasek/example.py',report['changed_sources'])
        self.assertTrue(report['potentially_affected']['architecture_review'])
        with self.assertRaises(KitError):
            docs.validate(self.root)
        docs.generate(self.root)
        self.assertFalse(docs.status(self.root)['stale'])

    def test_manual_source_is_preserved_and_edited_generated_page_blocks_overwrite(self):
        manual=(self.root/'documentation/content/index.md').read_bytes()
        docs.generate(self.root)
        output=self.root/docs.SITE/'index.md'
        output.write_text('# Cambio manual que debe conservarse\n',encoding='utf-8')
        with self.assertRaisesRegex(KitError,'editada'):
            docs.generate(self.root)
        self.assertIn('conservarse',output.read_text(encoding='utf-8'))
        self.assertEqual(manual,(self.root/'documentation/content/index.md').read_bytes())

    def test_unknown_file_in_generated_folder_is_never_deleted(self):
        docs.generate(self.root)
        path=self.put(docs.GENERATED+'/manual.md','# Conservar\n')
        with self.assertRaisesRegex(KitError,'manual inesperado'):
            docs.generate(self.root)
        self.assertTrue(path.exists())

    def test_removed_component_prunes_only_unchanged_owned_output(self):
        docs.generate(self.root)
        (self.root/'tools/example.py').unlink()
        docs.generate(self.root)
        self.assertFalse((self.root/docs.SITE/'generated/scripts/example.md').exists())
        self.assertTrue((self.root/'documentation/content/index.md').exists())

    def test_private_memory_audits_and_credentials_are_excluded(self):
        secret='sk-'+'A'*30
        self.put('project-memory/state.json',json.dumps({'private':secret}))
        self.put('.uasek/eip/approvals/private.json',json.dumps({'approval':'private'}))
        self.put('docs/quality/evidence/audit.json',json.dumps({'private':secret}))
        self.put('.env','PRIVATE_DATA='+secret)
        inputs=docs.discover(self.root)
        self.assertFalse(any(p.startswith(('project-memory/','.uasek/','docs/quality/evidence/')) for p in inputs))
        outputs,_,_=docs.expected(self.root)
        self.assertFalse(any(secret in content for content in outputs.values()))

    def test_secret_like_public_source_is_rejected_before_writing(self):
        self.put('docs/guide.md','# No publicar\n'+'sk-'+'A'*30+'\n')
        with self.assertRaisesRegex(KitError,'secreto'):
            docs.generate(self.root)
        self.assertFalse((self.root/docs.MANIFEST).exists())

    def test_source_link_traversal_and_unknown_versions_fail_closed(self):
        self.put('README.md','# Proyecto\n\n[Fuga](../../outside.md)\n')
        with self.assertRaises(KitError):
            docs.generate(self.root)
        self.put('README.md','# Proyecto\n')
        self.put(docs.MANIFEST,json.dumps({'schema_version':2,'sources':{},'outputs':{}}))
        with self.assertRaisesRegex(KitError,'incompatible'):
            docs.generate(self.root)

    def test_broken_source_and_generated_navigation_destinations_fail_validation(self):
        self.put('README.md','# Proyecto\n\n[Ausente](missing.md)\n')
        with self.assertRaisesRegex(KitError,'roto'):
            docs.generate(self.root)
        self.put('README.md','# Proyecto\n')
        (self.root/'documentation/content/security/overview.md').unlink()
        docs.generate(self.root)
        with self.assertRaisesRegex(KitError,'Navegación'):
            docs.validate(self.root)

    def test_rogue_portal_markdown_and_private_static_file_are_rejected(self):
        docs.generate(self.root)
        rogue=self.put(docs.PORTAL+'/private.md','# No permitir\n')
        with self.assertRaisesRegex(KitError,'sin fuente'):
            docs.validate(self.root)
        rogue.unlink()
        self.put(docs.PORTAL+'/public/state.json','{"private":true}')
        with self.assertRaisesRegex(KitError,'no permitido'):
            docs.validate(self.root)

    def test_post_build_checks_base_assets_and_heading_fragments(self):
        folder=docs.PORTAL+'/.vitepress/dist/'
        self.put(folder+'index.html','<html><a href="/repo/guide.html#chapter">Ir</a><script src="/repo/assets/app.js"></script></html>')
        self.put(folder+'guide.html','<html><h1 id="chapter">Guía</h1></html>')
        self.put(folder+'assets/app.js','console.log("local")')
        self.assertEqual(docs.validate_build(self.root,'/repo/')['html_pages'],2)
        with self.assertRaises(KitError):
            docs.validate_build(self.root,'/')
        self.put(folder+'guide.html','<h1 id="other">Otro</h1>')
        with self.assertRaisesRegex(KitError,'Ancla'):
            docs.validate_build(self.root,'/repo/')

    def test_post_build_rejects_unexpected_private_artifact(self):
        folder=docs.PORTAL+'/.vitepress/dist/'
        self.put(folder+'index.html','<h1>Portal</h1>')
        self.put(folder+'state.json','{"private":true}')
        with self.assertRaisesRegex(KitError,'privado'):
            docs.validate_build(self.root,'/')

    def test_unregistered_agent_is_reported_and_cannot_pass_validation(self):
        self.put('agents/new-agent/AGENT.md','# Agente nuevo\n')
        docs.generate(self.root)
        report=docs.scan(self.root)
        self.assertTrue(report['unregistered_or_missing_contracts'])
        with self.assertRaisesRegex(KitError,'sin contrato'):
            docs.validate(self.root)

    def test_catalog_path_traversal_and_duplicate_skill_ids_are_rejected(self):
        self.put('configs/catalog.json',json.dumps([{'id':'../../outside','name':'Inválido','path':'README.md'}]))
        with self.assertRaisesRegex(KitError,'ID de referencia'):
            docs.generate(self.root)
        self.put('configs/catalog.json','[]')
        self.put('skills/another/sample/SKILL.md','# Duplicada\n')
        with self.assertRaisesRegex(KitError,'duplicados'):
            docs.generate(self.root)

    def test_derived_portal_artifacts_do_not_stale_source_tests_but_theme_changes_do(self):
        before=operations.source_fingerprint(self.root)
        docs.generate(self.root)
        self.put('documentation/reports/build.json','{"generated":true}')
        self.assertEqual(before,operations.source_fingerprint(self.root))
        self.put(docs.PORTAL+'/.vitepress/theme/style.css',':root{color:green}')
        self.assertNotEqual(before,operations.source_fingerprint(self.root))

    def test_supervised_build_requires_approval_before_any_generation_or_process(self):
        from uasek.eip import store, governance
        memory.save(self.root,memory.initial('Proyecto'))
        store.initialize(self.root)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(docs.main(['build','--root',str(self.root)]),2)
        self.assertFalse((self.root/docs.MANIFEST).exists())
        output=io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(docs.main(['build','--root',str(self.root),'--policy-preview']),0)
        scope=json.loads(output.getvalue())
        self.assertEqual(scope['permission'],'execute')
        approval=governance.grant(self.root,'execute',scope['resource'],'Revisor','Build local revisado',True)['approval']
        with patch.object(docs,'build',return_value={'valid':True}) as build, redirect_stdout(io.StringIO()):
            self.assertEqual(docs.main(['build','--root',str(self.root),'--platform-approval',approval]),0)
            build.assert_called_once()
        with redirect_stderr(io.StringIO()):
            self.assertEqual(docs.main(['build','--root',str(self.root),'--platform-approval',approval]),2)

    def test_consultative_generation_and_changed_source_approval_are_enforced(self):
        from uasek.eip import store, governance
        from uasek.context_format import digest
        memory.save(self.root,memory.initial('Proyecto'))
        store.initialize(self.root)
        policy=governance.policy(self.root)
        policy['level']='consultivo'
        approval=governance.grant(self.root,'policy.change',digest(policy),'Revisor','Nivel consultivo',True)['approval']
        governance.configure(self.root,'policy',policy,approval)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(docs.main(['generate','--root',str(self.root)]),2)
        self.assertFalse((self.root/docs.MANIFEST).exists())
        output=io.StringIO()
        with redirect_stdout(output):
            docs.main(['generate','--root',str(self.root),'--policy-preview'])
        scope=json.loads(output.getvalue())
        self.assertEqual(scope['permission'],'memory.write')
        approval=governance.grant(self.root,'memory.write',scope['resource'],'Revisor','Generación revisada',True)['approval']
        self.put('docs/guide.md','# Contenido cambiado después de aprobar\n')
        with redirect_stderr(io.StringIO()):
            self.assertEqual(docs.main(['generate','--root',str(self.root),'--platform-approval',approval]),2)
        self.assertFalse((self.root/docs.MANIFEST).exists())


if __name__=='__main__':
    unittest.main()
