# Orchestrator

Dividir la solicitud en tareas verificables y asignar solo los roles necesarios.

Contrato canónico: [configs/agents.json](../../configs/agents.json), clave `orchestrator`.

Entregable: Plan con dependencias, encargos y consolidación de evidencias.

Skills: agent-orchestration, context-management.

Aceptación: Cada tarea tiene responsable, criterio verificable y dependencias satisfechas.

Escalar: Dependencias circulares, alcance contradictorio o decisiones sin propietario.

Ejecutar `python kit.py agent show --name orchestrator` para leer herramientas, restricciones, entradas y protocolo completo. Estos son perfiles operativos; el kit no crea procesos de IA autónomos por listar agentes.
