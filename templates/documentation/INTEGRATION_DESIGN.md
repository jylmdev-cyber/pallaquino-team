# Plantilla: Integraciones

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/architecture/INTEGRATION_DESIGN.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: OSV: POST https://api.osv.dev/v1/query con paquete/ecosistema/versión exacta y --online. PyPI: GET metadatos JSON; npm: GET registro, dist-tags.latest. Ollama: POST local /api/generate, stream false, 60 s. No hay clientes cloud ni webhooks. Toda salida de proveedor es texto no ejecutable. Fallos de red retornan error y se distinguen de ausencia de vulnerabilidades.
