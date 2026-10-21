# Persistencia

No hay servidor de base de datos. state.json es canónico; mantener schema_version=1. Guardado atómico del archivo y lock evitan escrituras simultáneas cooperantes. Un editor externo no respeta el lock: cerrar ediciones durante mutaciones. Vistas Markdown son derivadas y pueden regenerarse. Guardar estado en Git solo después de revisar datos sensibles.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
