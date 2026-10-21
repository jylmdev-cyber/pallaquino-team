# Plantilla: Requisitos no funcionales

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/business/NON_FUNCTIONAL_REQUIREMENTS.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: RNF-01: sin dependencias externas runtime, Python >=3.11. RNF-02: rutas de evidencia dentro del proyecto. RNF-03: HTTP con timeout y respuesta máxima 5 MB. RNF-04: walker no sigue symlinks/junctions. RNF-05: memoria con lock y archivo JSON atómico. RNF-06: Windows validado localmente; Linux/macOS pendientes de CI. No se declara capacidad de miles de escritores concurrentes ni sincronización distribuida.
