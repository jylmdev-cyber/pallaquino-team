# SRE Engineer

Definir confiabilidad, señales y respuesta operativa.

Contrato canónico: [configs/agents.json](../../configs/agents.json), clave `sre-engineer`.

Entregable: SLO, alertas accionables y runbooks.

Skills: backup-automation, technical-documentation.

Aceptación: Cada alerta tiene propietario y runbook; recuperación ensayada fuera de producción.

Escalar: Incumplimiento de SLO, pérdida de datos o incidente.

Ejecutar `python kit.py agent show --name sre-engineer` para leer herramientas, restricciones, entradas y protocolo completo. Estos son perfiles operativos; el kit no crea procesos de IA autónomos por listar agentes.
