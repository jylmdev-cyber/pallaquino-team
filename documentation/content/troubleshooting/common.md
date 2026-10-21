# Resolver problemas

## No se encuentra Python o npm

Comprueba `python --version` y `node --version`. En Windows puedes usar `py -3`; en Unix, `python3`. El núcleo necesita Python 3.11+; el portal fija Node 24.22.x y sus dependencias en un lockfile. Ejecuta `npm ci --ignore-scripts` dentro de `documentation/portal`.

## La documentación está desactualizada

```console
python tools/docs_manager.py scan
python tools/docs_manager.py generate
python tools/docs_manager.py validate
```

Revisa las fuentes modificadas y los diagramas indicados. Si una salida generada fue editada manualmente, el generador se detiene: conserva tus cambios, llévalos a la fuente correspondiente y restaura solo ese archivo generado desde su fuente conocida después de revisarlo. No borres la documentación manual para resolver el bloqueo.

## El build muestra un enlace o ancla inexistente

Corrige el destino en la fuente original y regenera. Los enlaces entre fuentes reutilizadas se convierten a rutas del portal; los archivos no publicados se identifican como referencias locales. Las referencias públicas al código usan el repositorio. No silencies la validación de enlaces.

## Página o recursos con error 404 en Pages

Verifica que la base del proyecto sea `/pallaquino-team/`. Para dominio personalizado utiliza `/`. Después reconstruye y ejecuta `validate-build --base /ruta/`. Comprueba que el artefacto publicado sea `.vitepress/dist` y que Pages use GitHub Actions. La URL prevista no confirma que el sitio esté desplegado.

## El workflow no publica

Es el comportamiento predeterminado. Se necesita autorización, configuración de Pages, la variable `UDP_PAGES_ENABLED=true` y rama `main`; manualmente, también `publish=true`. Los eventos de PR no publican. Revisa permisos del entorno `github-pages` y el resultado real del job.

## No aparece un diagrama o falla la búsqueda

Usa un servidor HTTP local, no abras el HTML mediante `file://`. Los módulos de búsqueda y Mermaid se cargan como recursos estáticos; revisa su base y consola. La fuente textual de cada diagrama está disponible aunque falle su dibujo. Regenera después de modificar contratos o catálogos.

## EIP rechaza una acción

Consulta `--policy-preview`, el nivel del proyecto y el recurso exacto. Una aprobación puede caducar, consumirse o dejar de coincidir si cambian las entradas. No eleves la autonomía para ocultar el problema. Si hay conflicto, revisa candidato, journal y checkpoint.

[Problemas del núcleo](/generated/reference/docs/operations/TROUBLESHOOTING.html) · [Administrar el portal](/generated/reference/documentation/PORTAL_MANUAL.html)
