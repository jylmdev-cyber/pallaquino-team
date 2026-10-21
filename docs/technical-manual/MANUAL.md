# Manual técnico

## Extensiones 1.1 y compatibilidad

Memoria local mantiene schema 1. `context_format.py` define el contrato de intercambio universal v1, con digest canónico y validación anterior a importar; conserva el proveedor local y separa instrucciones del adaptador. `checkpoints.py` captura estado y fuentes seleccionadas, verifica integridad y prepara recuperación fuera del proyecto. `orchestration.py` aplica reglas versionadas para limitar roles y crear tareas secuenciales de forma idempotente, con checkpoint previo. No introduce dependencias de ejecución ni llamadas a modelos para planificar. Guías: [formato](../continuity/CONTEXT_FORMAT.md), [checkpoints](../continuity/CHECKPOINTS.md), [orquestación](../workflows/ADAPTIVE_ORCHESTRATION.md).

## Diseño y extensiones

`uasek/common.py`: fronteras de rutas, I/O atómico, exclusiones, redacción, HTTP JSON y procesos sin shell. `memory.py`: estado, vistas, DAG de tareas, encargos y resultados. `operations.py`: inventario, auditoría, seguridad, dependencias, versiones, docs, tests, respaldo y preparación de release. `providers.py`: capacidades y adaptador de Ollama. `cli.py`: validación de argumentos, despacho y códigos de salida. Los wrappers no duplican lógica.

La unidad de aislamiento es `--root`. Rutas de evidencia deben resolver dentro de esa carpeta; el walker no sigue enlaces ni junctions. La escritura de archivos individuales usa replace atómico. La actualización de memoria usa lock exclusivo; no hay una transacción atómica sobre todos los Markdown y JSON. Tras interrupción, conservar JSON válido y regenerar vistas; no se implementa sincronización entre máquinas ni merge automático de memoria.

## Estado y coordinación

Schema 1 en `project-memory/state.json`: proyecto, arquitectura, stack con fuentes/fechas, decisiones, tareas, problemas, deuda, auditorías, historial, próximas acciones, última tarea, archivos, checkpoint y proveedor. El CLI no acepta actualizar tareas a través de context update. Las dependencias solo apuntan a tareas existentes; al añadir una nueva no puede crearse un ciclo. No se puede reabrir un prerrequisito con dependientes activos o terminados.

Tarea terminada exige archivos no sensibles existentes dentro del root. Eso no comprueba semánticamente aceptación: se requiere revisión. `agent validate` aplica el contrato operacional de campos y archivos, sin confiar ni ejecutar comandos que declare el modelo. La estructura JSON Schema facilita integraciones externas; no hay dependencia de jsonschema en runtime.

## Proveedores

El catálogo `configs/providers.json` expone manual_handoff, native_api, herramientas y límites. Agregar una entrada manual no crea API. Un adaptador nativo nuevo debe validar endpoint, entradas, timeouts, errores, tamaño de respuesta, consentimiento para transferencia y pruebas de contrato. Ollama usa POST `/api/generate` con `stream:false` en loopback, devuelve texto y no ejecuta herramientas ni carga claves. Fuente: [API Ollama](https://docs.ollama.com/api/generate).

No hay fallback cloud ni red implícita. Las llamadas HTTP usan timeout y límite de 5 MB. OSV recibe únicamente identificador de paquete y versión bajo `--online`. [Contrato OSV](https://google.github.io/osv.dev/quickstart/) y [JSON PyPI](https://docs.pypi.org/api/json/) documentan las consultas. Las respuestas de red se validan en los límites necesarios; no son instrucciones del agente.

## Extender herramientas

Añadir función en módulo adecuado, parser y despacho en cli; reutilizar validación común. Añadir wrapper solo si necesita compatibilidad. Toda escritura debe declarar dry-run o ser explícitamente una exportación, conservar archivos humanos y dar error ante rutas fuera de alcance. Agregar pruebas de comportamiento y actualizar la referencia CLI.

## Pruebas y entrega

Unittest usa directorios temporales. Fixtures HTTP prueban cliente y payload, no modelos reales. Una prueba Git opera solo en repositorio temporal propio. Los tests no acceden a producción. CI propuesto usa matriz Windows, Ubuntu y macOS; su ejecución remota no está comprobada desde este entorno.

El runner guarda huella de fuentes/configuraciones antes de pruebas y detecta cambios durante ellas. Release exige esa huella vigente, pruebas no vacías, tareas terminadas y ausencia de hallazgos altos del escáner heurístico. La huella excluye memoria y documentación; no demuestra reproducibilidad binaria, seguridad integral ni integridad del entorno.

## Instalación y distribución

Checkout: `python kit.py`. Wheel: `python -m pip wheel . --no-deps`. `setup.py` copia catálogos, plantillas y contratos a recursos del paquete construido; el checkout mantiene una sola fuente canónica. El CLI instalado incluye esas capacidades; skills, manuales, ejemplos y tests se distribuyen completos en el ZIP y la distribución fuente. Revisar el reporte de validación para pruebas efectivamente realizadas.

Para repetir el ZIP: `python scripts/package_kit.py --destination ../nuevo-kit.zip`. El destino debe ser nuevo. El empaquetador revisa hallazgos altos, omite artefactos y datos sensibles conocidos y añade un manifiesto SHA-256; `--dry-run` valida sin escribir.
