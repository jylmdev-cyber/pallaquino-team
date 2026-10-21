# Motor documental: decisión UDP-001

Fecha de revisión: 2026-10-21. Proyecto: PALLAQUINO TEAM. Alcance: portal estático público preparado, sin despliegue durante esta entrega.

## Alternativas revisadas

| Motor | Línea estable consultada | Evaluación para este repositorio |
|---|---|---|
| VitePress | 1.6.4; 2.0 continúa como alpha | Markdown, búsqueda local, temas, resaltado, copia, navegación y build estático; capa Node separada del núcleo Python |
| Astro Starlight | 0.42.6 | Alternativa especializada y accesible; añadiría convenciones Astro sin necesidad funcional adicional aquí |
| Docusaurus | 3.10.2 | Versionado e internacionalización completos; una capa React mayor para el alcance inicial en español |
| MkDocs Material | 9.7.7 | Integración Python adecuada, pero mantenimiento limitado y fin de soporte anunciado para mayo de 2027 |

Las versiones se comprobaron en los registros oficiales npm/PyPI y la documentación de los proyectos. No se instalaron estos cuatro frameworks: solo VitePress. Zensical se revisó como sucesor de Material; su línea aún está en evolución y no se usa en esta entrega.

## Selección

**VitePress 1.6.4**, con Vue y Mermaid fijados, lockfile npm y Node 24.22.x. Búsqueda local sin backend ni terceros. Diagramas renderizados en cliente con nivel de seguridad estricto, fuente textual y controles de escala. El build produce HTML y recursos estáticos compatibles con la base de GitHub Pages.

Las páginas se generan desde fuentes existentes y guías manuales con un administrador Python estándar. No se introducen dependencias Node en la CLI Python. El generador inspecciona AST y el parser argparse de confianza; no ejecuta scripts descubiertos. El público inicial es hispanohablante; se configura `es-PE`. No se inventan traducciones ni se afirma multilenguaje implementado; añadir otro idioma requiere rutas, navegación y revisión propias.

El versionado identifica el software actual y conserva reportes anteriores; no se generan falsos snapshots de documentación antigua. WCAG 2.2 AA es objetivo de diseño, no una certificación.

## Corrección de la dependencia de build

La auditoría npm inicial detectó advisories en Vite/esbuild heredados por VitePress 1.6.4. Se fija mediante `overrides` Vite **6.4.4**, compatible con el peer declarado del plugin Vue incluido. Su resolución elimina esos avisos en la auditoría ejecutada; la compatibilidad real se verifica con build y navegador, sin recurrir a una versión alpha de VitePress. Conservar esta excepción explícita y repetir ambas comprobaciones al actualizar.

## Fuentes oficiales

- [VitePress: despliegue estable 1.x](https://vuejs.github.io/vitepress/v1/guide/deploy).
- [VitePress: búsqueda local](https://vuejs.github.io/vitepress/v1/reference/default-theme-search).
- [Astro: GitHub Pages](https://docs.astro.build/en/guides/deploy/github/).
- [Docusaurus: despliegue](https://docusaurus.io/docs/deployment).
- [Material: historial y mantenimiento](https://squidfunk.github.io/mkdocs-material/changelog/).
- [Zensical: compatibilidad](https://zensical.org/docs/compatibility/mkdocs/).

## Actualización

Revisar versiones y advisories antes de cada actualización. Usar cambios revisados en manifiesto y lockfile, repetir auditoría, build y pruebas de navegador. Los informes de validación distinguen resultados locales, comprobaciones automatizadas y configuración externa pendiente.
