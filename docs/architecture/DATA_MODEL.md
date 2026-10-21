# Modelo de datos

Schema 1: project es objeto de identidad/requisitos; tasks es lista con id, title, agent, acceptance, depends_on, status, evidence y timestamps. Las dependencias referencian IDs existentes. Los campos architecture, stack, decisions, known_issues, technical_debt, audits, history y next_actions preservan contexto. provider tiene name/mode. validated_checkpoint es referencia textual revisada, no una certificación. Consulte project-memory/state.json.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
