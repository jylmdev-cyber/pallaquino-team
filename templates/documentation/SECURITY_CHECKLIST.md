# Plantilla: Controles de seguridad

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/quality/SECURITY_CHECKLIST.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: Revisar rutas, datos no confiables, privilegios y secretos. scan es heurístico y no cubre binarios o archivos >1 MB. Backups de fuentes omiten archivos sensibles, pero no sustituyen almacenamiento cifrado. Auditar dependencias requiere versión exacta y consulta explícita; formatos desconocidos no son seguros por defecto. No se incluyen operaciones de borrado, reset, push, despliegue o restauración destructiva. Referencia: docs/standards/REFERENCES.md.
