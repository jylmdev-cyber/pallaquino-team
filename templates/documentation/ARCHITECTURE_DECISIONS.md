# Plantilla: Decisiones arquitectónicas

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/architecture/ARCHITECTURE_DECISIONS.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: ADR-001 aceptada: biblioteca estándar para reducir instalación y superficie runtime. Consecuencia: dependencias avanzadas y validación de versiones quedan acotadas. ADR-002 aceptada: JSON canónico y Markdown derivado; permite revisión Git pero no transacciones entre múltiples archivos. ADR-003 aceptada: transferencia manual cloud para no fingir APIs ni permisos. ADR-004 aceptada: DAG incremental sin edición de dependencias; simplifica aciclicidad y reanudación.
