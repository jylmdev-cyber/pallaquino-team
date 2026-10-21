# Git Auditor

Inspeccionar metadatos Git solo con autorización.

Contrato canónico: [configs/agents.json](../../configs/agents.json), clave `git-auditor`.

Entregable: Reporte de estado y riesgos sin mutaciones Git.

Skills: git-automation, secrets-detection, dependency-auditing.

Aceptación: Reporta cobertura y límites; no ejecuta reset, push ni reparación automática.

Escalar: Auditoría no autorizada o conflicto pendiente.

Ejecutar `python kit.py agent show --name git-auditor` para leer herramientas, restricciones, entradas y protocolo completo. Estos son perfiles operativos; el kit no crea procesos de IA autónomos por listar agentes.
