# Integraciones

OSV: POST https://api.osv.dev/v1/query con paquete/ecosistema/versión exacta y --online. PyPI: GET metadatos JSON; npm: GET registro, dist-tags.latest. Ollama: POST local /api/generate, stream false, 60 s. No hay clientes cloud ni webhooks. Toda salida de proveedor es texto no ejecutable. Fallos de red retornan error y se distinguen de ausencia de vulnerabilidades.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
