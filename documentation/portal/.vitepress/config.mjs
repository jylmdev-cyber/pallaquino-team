import { defineConfig } from 'vitepress'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const generated = JSON.parse(fs.readFileSync(path.join(here, 'generated.json'), 'utf8'))
const repository = process.env.GITHUB_REPOSITORY || 'jylmdev-cyber/pallaquino-team'
if (!/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(repository)) throw new Error('GITHUB_REPOSITORY inválido')
const [owner, repo] = repository.split('/')
const base = process.env.DOCS_BASE || (repo.toLowerCase() === `${owner.toLowerCase()}.github.io` ? '/' : `/${repo}/`)
if (!/^\/(?:[a-zA-Z0-9_.-]+\/)*$/.test(base)) throw new Error('DOCS_BASE requiere una ruta absoluta terminada en /')
const origin = process.env.DOCS_ORIGIN || `https://${owner}.github.io`
if (!/^https:\/\/[a-zA-Z0-9.-]+(?::[0-9]+)?$/.test(origin)) throw new Error('DOCS_ORIGIN requiere un origen HTTPS sin ruta')

export default defineConfig({
  title: 'PALLAQUINO TEAM',
  description: 'Documentación de la plataforma de ingeniería asistida por IA: contexto, agentes y automatización con control.',
  lang: 'es-PE', base,
  srcDir: 'generated/site',
  vite: { publicDir: path.resolve(here, '../public') },
  srcExclude: ['node_modules/**', 'package*.json'],
  cleanUrls: false,
  lastUpdated: false,
  head: [['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}logo.svg` }]],
  sitemap: { hostname: origin + base.replace(/\/$/, '') },
  themeConfig: {
    logo: '/logo.svg', siteTitle: 'PALLAQUINO TEAM',
    nav: [
      { text: 'Guías', link: '/introduction/overview' },
      { text: 'Plataforma', link: '/generated/reference/docs/platform/PLATFORM' },
      { text: 'Catálogos', items: [
        { text: 'Agentes', link: '/generated/agents/index' },
        { text: 'Skills', link: '/generated/skills/index' },
        { text: 'Ejemplos por rubro', link: '/generated/examples/index' }
      ] },
      { text: `v${generated.version}`, items: [
        { text: 'Historial y compatibilidad', link: '/changelog/versions' },
        { text: 'Changelog', link: '/generated/reference/docs/continuity/CHANGELOG' }
      ] }
    ],
    sidebar: generated.sidebar,
    outline: { level: [2, 3], label: 'En esta página' },
    docFooter: { prev: 'Anterior', next: 'Siguiente' },
    darkModeSwitchLabel: 'Cambiar tema', lightModeSwitchTitle: 'Usar tema claro', darkModeSwitchTitle: 'Usar tema oscuro',
    sidebarMenuLabel: 'Secciones', returnToTopLabel: 'Volver arriba',
    search: { provider: 'local', options: { locales: { root: { translations: {
      button: { buttonText: 'Buscar documentación', buttonAriaLabel: 'Buscar documentación' },
      modal: { noResultsText: 'Sin resultados para', resetButtonTitle: 'Limpiar búsqueda',
        footer: { selectText: 'seleccionar', navigateText: 'navegar', closeText: 'cerrar' } }
    } } } } },
    socialLinks: [{ icon: 'github', link: `https://github.com/${repository}` }],
    footer: { message: 'Contexto compartido. Decisiones trazables. Control humano.', copyright: 'PALLAQUINO TEAM · Licencia MIT' }
  },
  markdown: {
    lineNumbers: true,
    config(md) {
      const fallback = md.renderer.rules.fence
      md.renderer.rules.fence = (tokens, idx, options, env, self) => {
        if (tokens[idx].info.trim() === 'mermaid') {
          return `<Diagram source="${encodeURIComponent(tokens[idx].content).replace(/'/g, '%27')}" />\n`
        }
        return fallback(tokens, idx, options, env, self)
      }
    }
  }
})
