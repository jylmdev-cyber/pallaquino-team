# Administrar el portal de PALLAQUINO TEAM

UDP edición 1 documenta el software 2.0.0. El nombre de presentación es PALLAQUINO TEAM; los identificadores técnicos del núcleo se conservan por compatibilidad. El portal es público por diseño, con build estático y publicación remota deshabilitada hasta autorización.

Consultar el [reporte de validación](content/quality/validation.md) para distinguir funciones implementadas, comprobadas y pendientes de configuración externa.

## 1. Instalar

Necesitas Python 3.11+ y Node 24.22.x. Desde la raíz del repositorio:

```console
python tools/docs_manager.py generate
cd documentation/portal
npm ci --ignore-scripts
```

El lockfile fija dependencias transitivas. El núcleo Python no necesita npm para funcionar. No uses instalaciones globales de VitePress ni añadas otro generador para el mismo portal.

Si EIP está activa en la raíz objetivo, UDP respeta su política: `generate` y guardar informes requieren `memory.write`; `build` y `prepare-deploy` requieren `execute`. En nivel supervisado el build necesita una aprobación acotada. Usa `python tools/docs_manager.py build --policy-preview` para obtener el recurso y el flujo `platform approve` documentado en EIP; después repite el comando con `--platform-approval AP-ID`. La aprobación es de un solo uso y queda invalidada si cambian las fuentes. Preparar el artefacto nunca equivale a permiso de despliegue.

## 2. Ejecutar localmente

Dentro de `documentation/portal`:

```console
npm run dev
```

Abre la URL impresa, normalmente en el puerto 5173. La base configurada es `/pallaquino-team/`. Para ver el build final:

```console
npm run preview -- --port 4173
```

Usa HTTP local, no `file://`; la búsqueda y los diagramas cargan módulos JavaScript. Para regenerar fuentes mientras desarrollas, ejecuta `generate` desde otra terminal en la raíz.

## 3. Modificar la página principal

Edita `documentation/content/index.md`. Su frontmatter define hero, acciones y tarjetas; `PortalStatus.vue` obtiene versión y conteos reales del índice generado. La identidad visual está en `documentation/portal/.vitepress/theme/style.css`; el logotipo en `public/logo.svg`. No edites `documentation/portal/generated/site/index.md`: es una salida derivada protegida. Todo el contenido derivado se concentra en `generated/`, excluido del control de versiones.

## 4. Agregar documentación

Crea un Markdown en `documentation/content/SECCION/`. Regenera y enlázalo desde una guía existente. Para incorporarlo a la navegación principal, modifica `SECTIONS` o el árbol de navegación del generador en `uasek/documentation.py`. Para documentación ya existente en `docs/`, edita la fuente original: el generador la reutiliza automáticamente.

```console
python tools/docs_manager.py scan
python tools/docs_manager.py generate
python tools/docs_manager.py validate
```

Los archivos manuales nunca se sobrescriben. Si alguien edita una salida derivada, el hash no coincide y la generación se detiene. Conserva esos cambios, trasládalos a su fuente y restaura solo la salida afectada de forma revisada. Un archivo inesperado en la carpeta generada también bloquea la regeneración. No copies memoria ni secretos a las fuentes públicas.

## 5. Incorporar agentes y skills

Agentes: mantener contrato en `configs/agents.json` y su documentación en `agents/`. Skills: un `SKILL.md` por carpeta bajo `skills/`, con nombre único. El índice deriva las compatibilidades de la lista `skills` de cada agente. Agregar una entrada no inicia un modelo ni concede permisos. `generate` reconstruye catálogos y navegación desde las fuentes; `scan` detecta su cambio.

Sistemas por rubro: mantener `configs/catalog.json` y `templates/systems/ID/SYSTEM.md`. Cada referencia se publica con sus límites de implementación.

## 6. Actualizar diagramas

Edita bloques `mermaid` en las fuentes Markdown. Para la arquitectura transversal, usa `documentation/content/architecture/overview.md`; los flujos están en desarrollo, automatización, seguridad e integraciones. Marca los diagramas propuestos como tales. El componente usa Mermaid empaquetado, sin CDN, y `securityLevel: strict`. Ofrece controles de escala y fuente textual accesible. Cambios de código solo sugieren revisión de arquitectura; el generador no corrige diagramas por adivinación.

## 7. Validar

```console
python tools/docs_manager.py scan
python tools/docs_manager.py status
python tools/docs_manager.py validate
python -m unittest discover -s tests -v
```

`status` es de lectura y muestra deriva de fuentes/salidas. `validate` requiere fuentes sincronizadas, comprueba rutas, fichas y navegación. Las firmas Python se leen con AST; no se importan los módulos para descubrir APIs. El parser CLI conocido se inspecciona sin ejecutar comandos.

`scan` informa cobertura estructural, no exactitud semántica ni porcentaje de negocio completo. El generador no ejecuta scripts encontrados ni consulta servicios de IA. La búsqueda del navegador es local.

## 8. Generar el build y preparar artefactos

Desde la raíz, con dependencias instaladas:

```console
python tools/docs_manager.py build
python tools/docs_manager.py prepare-deploy
```

Ambos generan y validan; después ejecutan VitePress y revisan HTML, anclas, rutas de recursos y base. `prepare-deploy` añade `.nojekyll`. Ninguno realiza commit, push, cambios remotos o despliegue. El artefacto está en `documentation/portal/.vitepress/dist/`. Se excluyen memoria privada, aprobaciones, auditorías locales y credenciales por lista de fuentes permitidas.

Para guardar un informe nuevo sin sobrescribir otro:

```console
python tools/docs_manager.py scan --report documentation/reports/scan-local.json
```

El directorio de informes locales está ignorado por Git y no se publica.

Las salidas `generated/`, `.vitepress/generated.json`, cachés y reportes locales también se excluyen del inventario de fuentes, empaquetado y checkpoints del núcleo; se reconstruyen desde sus entradas. Cambios de tema, componentes y configuración sí participan en la huella de fuentes. Así, construir el portal no invalida por sí mismo las pruebas del software.

## 9. Configurar GitHub

Repositorio previsto: `jylmdev-cyber/pallaquino-team`, rama principal `main`. Los workflows usan Actions oficiales fijadas por commit. La CI de documentación requiere solo lectura; el job de despliegue tiene `pages: write` e `id-token: write`, únicamente cuando está habilitado. No se utiliza un token personal para publicar ni eventos `pull_request_target`.

Antes de publicar, el propietario debe revisar contenido público, dependencias y artefactos, autorizar los cambios remotos y comprobar sus permisos. Esta entrega no publica el portal.

## 10. Activar GitHub Pages

Después de la autorización:

1. En Settings → Pages, seleccionar Source **GitHub Actions**.
2. Revisar el entorno `github-pages` y, si procede, exigir aprobación de despliegue.
3. En Settings → Secrets and variables → Actions → Variables, crear `UDP_PAGES_ENABLED` con valor `true`.
4. Confirmar base `/pallaquino-team/` y origen HTTPS. Para otra raíz, definir `DOCS_BASE` y `DOCS_ORIGIN` como variables de repositorio; los workflows las transmiten al build.

Sin esa habilitación el job de publicación se omite, aunque se construya el artefacto. Para deshabilitar futuras publicaciones, retirar la variable o cambiarla a `false`.

## 11. Primer despliegue autorizado

Publicar los cambios únicamente tras la confirmación del propietario. En Actions, ejecutar **Documentation Pages** sobre `main` con `publish=true`, o utilizar el siguiente push autorizado a `main` después de habilitar Pages. Esperar el job, revisar la URL real devuelta por `deploy-pages` y comprobar inicio, búsqueda, navegación, diagramas y rutas de recursos. La URL prevista no sustituye esa verificación.

## 12. Actualizar el portal

Actualizar fuentes, regenerar, validar y construir. La CI se ejecuta en PR. Al integrarse en `main`, el workflow prepara el artefacto y publica solo si sigue habilitado. Los cambios en `uasek/`, contratos, skills, plantillas y documentación activan la validación; las fuentes no documentales relevantes se consideran en la cobertura.

## 13. Dominio personalizado

Autorizar y configurar el dominio en GitHub Pages y DNS según GitHub. Establecer `DOCS_BASE=/` y `DOCS_ORIGIN=https://docs.ejemplo.com`; si se necesita un archivo CNAME para la configuración elegida, mantener el dominio aprobado en `documentation/portal/public/CNAME`. No se incluye un dominio inventado. Reconstruir y ejecutar `validate-build --base /` antes de publicar.

## 14. Recuperar una versión anterior

Conservar los reportes históricos y referencias de commits. Preparar un checkout separado del commit elegido, instalar desde su lockfile, generar y validar antes de solicitar su publicación. No borrar ni reescribir el historial. Para recuperar fuentes del kit, usar checkpoints en una carpeta nueva y volver a ejecutar pruebas; no restaurar a ciegas sobre el árbol actual.

## 15. Resolver publicación y configuración

| Síntoma | Revisar |
|---|---|
| Job omitido | `UDP_PAGES_ENABLED`, rama `main`, evento e input manual `publish` |
| Pages responde 404 | Source GitHub Actions, permisos, artefacto y resultado real del job |
| CSS o búsqueda fallan | Base de proyecto, dominio y build actual; usar HTTP |
| Ancla rota | Encabezado de destino; corregir fuente y regenerar |
| Generación bloqueada | Fuente sensible, salida editada o archivo manual inesperado |
| Dependencias incompatibles | Node fijado, `npm ci --ignore-scripts`, lockfile y auditoría |
| Diagrama fallido | Sintaxis Mermaid, consola del navegador y fuente textual |

El objetivo de accesibilidad es WCAG 2.2 AA. Registrar verificaciones de teclado, móvil, contraste y búsqueda; no declarar certificación solo por compilar. El reporte de la entrega distingue lo implementado, probado y pendiente de configuración externa.

## QA opcional con navegador real

`documentation/scripts/browser_check.cjs` comprueba inicio, cambio de tema, búsqueda local, diagramas de todas las páginas, zoom, navegación móvil y foco. Requiere Playwright instalado en el entorno de QA, separado de las dependencias de producción, y un navegador compatible (Edge en Windows, Chromium de Playwright en otros entornos). No se instala ni descarga un navegador automáticamente.

Con un servidor preview activo y Playwright resoluble por Node:

```console
node documentation/scripts/browser_check.cjs
```

Por defecto usa `http://localhost:4173/pallaquino-team/` y escribe capturas e informe en `documentation/reports/browser/`. `PORTAL_URL` permite otra URL local y `PORTAL_QA_OUTPUT` otra carpeta de reportes. Solo admite localhost/127.0.0.1; usa un contexto nuevo, sin perfiles ni sesiones personales. Estas comprobaciones no son una auditoría WCAG completa.
