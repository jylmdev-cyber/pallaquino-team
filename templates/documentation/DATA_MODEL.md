# Plantilla: Modelo de datos

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/architecture/DATA_MODEL.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: Schema 1: project es objeto de identidad/requisitos; tasks es lista con id, title, agent, acceptance, depends_on, status, evidence y timestamps. Las dependencias referencian IDs existentes. Los campos architecture, stack, decisions, known_issues, technical_debt, audits, history y next_actions preservan contexto. provider tiene name/mode. validated_checkpoint es referencia textual revisada, no una certificación. Consulte project-memory/state.json.
