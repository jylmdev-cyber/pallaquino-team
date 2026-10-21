# Plantilla: Convenciones

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/development/CODING_STANDARDS.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: Python 3.11+, biblioteca estándar, procesos con argv y shell=False, errores esperados KitError y códigos no cero. Rutas mutables se resuelven con safe_path. Escribir archivos individuales atómicamente cuando corresponda y respetar locks de memoria. No imprimir secretos ni incorporar dependencias para una operación ya cubierta por stdlib. IDs de skills en minúsculas con guiones.
