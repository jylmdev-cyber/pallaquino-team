# Validación del portal UDP — edición 1

Proyecto: **PALLAQUINO TEAM**, software 2.0.0. Fecha: 2026-10-21. Entorno ejecutado: Windows, Python 3.12.10, Node 24.22.0, npm 11.19.1 y Chromium/Edge en un contexto de navegador nuevo. Publicación solicitada: pública preparada, sin desplegar.

## Resultado y evidencia ejecutada

| Comprobación | Resultado |
|---|---|
| Suite del proyecto | 137 pruebas: 136 aprobadas, 1 omitida por privilegios de symlink en Windows |
| Pruebas propias UDP | 17: generación, deriva, conservación manual, exclusión de privados, traversal, versiones, registro de contratos, duplicados, enlaces, huella de fuentes y permisos EIP |
| Instalación reproducible | `npm ci --ignore-scripts` completado desde el lockfile |
| Dependencias web | `npm audit` sin vulnerabilidades reportadas tras fijar Vite 6.4.4 |
| Build de proyecto | HTML estático, enlaces, anclas y recursos comprobados bajo `/pallaquino-team/` |
| Build de sitio de usuario/organización | Base `/` inferida desde un repositorio `propietario/propietario.github.io`; sitemap y recursos comprobados |
| Navegador real | Inicio HTTP, temas, búsqueda local, zoom, foco, menús y lateral móvil verificados; sin errores JS o respuestas HTTP fallidas |
| Diagramas | 71 diagramas renderizados en 37 páginas, incluidas las referencias sectoriales |
| Catálogos | 21 agentes, 31 skills, 30 referencias sectoriales, 19 scripts Python y 24 módulos Python derivados de fuentes reales |
| Datos privados | Memoria, aprobaciones, auditorías locales, `.env` y credenciales excluidos del build; escaneo heurístico sin hallazgos |
| GitHub remoto | Sin push, cambios remotos ni despliegue; workflows preparados y publicación deshabilitada por defecto |

El portal contiene 217 páginas de documentación y la página 404 del framework. Los índices y la versión se calculan desde las fuentes; estas cifras no son métricas inventadas de calidad o de uso.

Los informes completos de ejecución y capturas se conservan localmente en `documentation/reports/`, ignorados por Git y fuera del portal. El resumen revisado, sin rutas personales ni logs privados, se registra en `docs/quality/evidence/udp-validation.json` al cerrar la entrega. Los reportes históricos de UASEK conservan sus resultados originales y no sustituyen esta validación.

## Criterios de aceptación

| Criterio | Estado y alcance |
|---|---|
| Portal funcional y navegación | Implementado y probado localmente, con TOC, breadcrumbs, anterior/siguiente y búsqueda |
| Diseño responsive, tema y teclado | Probado a 1440px y 390px; capturas inspeccionadas y foco comprobado |
| Resaltado, comandos y tablas | Framework renderiza bloques, botón de copia y tablas con desplazamiento |
| Mermaid | Renderizado real de todas las páginas que contienen diagramas; fuente textual disponible |
| Catálogos y referencia CLI/API | Generados desde contratos, parser y AST; no se ejecutan scripts descubiertos |
| Documentación viva | Deriva por hashes y sugerencias de revisión; no evalúa automáticamente la corrección semántica de cada frase |
| Protección de documentación manual | Cambios manuales en fuentes conservados; edición inesperada de derivados bloquea regeneración |
| Integración con permisos EIP | Generación/build sujetos a política, preview sin ejecución y aprobaciones de un solo uso ligadas a fuentes públicas |
| Privacidad y permisos | Lista pública de entradas, rechazo de posibles secretos y gates remotos; no garantía universal de ausencia de secretos |
| CI/CD | YAML y controles revisados localmente; ejecución en GitHub pendiente |
| GitHub Pages | Configuración y artefacto preparados; servicio remoto sin activar ni verificar |
| Manual | Instalación, contenido, catálogos, diagramas, validación, build, Pages, dominio y recuperación documentados |

## Límites de la validación

WCAG 2.2 AA es un objetivo. Las comprobaciones de teclado, móvil y revisión visual no son una auditoría completa de lector de pantalla, contraste de todos los estados o certificación formal. No se ejecutó CI Linux/macOS en este trabajo. No se publicaron dominios personalizados ni se modificó DNS.

La auditoría npm depende de los avisos disponibles en la fecha ejecutada. Los controles de contenido son heurísticos y la revisión humana del artefacto sigue siendo necesaria. El build estático no necesita backend, claves ni analítica externa. Los proveedores de IA y despliegues de aplicaciones mantienen sus límites ya documentados en EIP.

## Reproducir

```console
python tools/docs_manager.py generate
python tools/docs_manager.py validate
python tools/docs_manager.py prepare-deploy
python kit.py test
```

Instalar antes las dependencias con `npm ci --ignore-scripts` en `documentation/portal`. Para QA de navegador, iniciar preview y utilizar el script descrito en el [manual del portal](/generated/reference/documentation/PORTAL_MANUAL.html). El pipeline no publica hasta la habilitación y autorización del propietario.
