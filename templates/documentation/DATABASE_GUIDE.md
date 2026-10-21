# Plantilla: Persistencia

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/development/DATABASE_GUIDE.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: No hay servidor de base de datos. state.json es canónico; mantener schema_version=1. Guardado atómico del archivo y lock evitan escrituras simultáneas cooperantes. Un editor externo no respeta el lock: cerrar ediciones durante mutaciones. Vistas Markdown son derivadas y pueden regenerarse. Guardar estado en Git solo después de revisar datos sensibles.
