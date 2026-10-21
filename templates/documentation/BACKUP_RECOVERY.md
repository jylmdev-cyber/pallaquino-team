# Plantilla: Respaldo y recuperación

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/operations/BACKUP_RECOVERY.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: backup crea ZIP de textos seleccionados, MANIFEST.json y hashes SHA-256. Omite binarios, BD, archivos >5 MB, secretos detectados y carpetas excluidas. Destino debe ser nuevo. Recuperar inspeccionando nombres y hashes y extrayendo en carpeta nueva; no hay restore automático. Para bases y secretos usar respaldo cifrado y pruebas de recuperación de la plataforma elegida.
