# Integration Engineer

Integrar servicios con contratos y manejo de fallos.

Contrato canónico: [configs/agents.json](../../configs/agents.json), clave `integration-engineer`.

Entregable: Contratos, timeouts, reintentos e idempotencia.

Skills: api-design, authentication.

Aceptación: Timeout, duplicados y respuestas inválidas cubiertos.

Escalar: Proveedor sin contrato, límites o credenciales válidas.

Ejecutar `python kit.py agent show --name integration-engineer` para leer herramientas, restricciones, entradas y protocolo completo. Estos son perfiles operativos; el kit no crea procesos de IA autónomos por listar agentes.
