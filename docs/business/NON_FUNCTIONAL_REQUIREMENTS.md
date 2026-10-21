# Requisitos no funcionales

RNF-01: sin dependencias externas runtime, Python >=3.11. RNF-02: rutas de evidencia dentro del proyecto. RNF-03: HTTP con timeout y respuesta máxima 5 MB. RNF-04: walker no sigue symlinks/junctions. RNF-05: memoria con lock y archivo JSON atómico. RNF-06: Windows validado localmente; Linux/macOS pendientes de CI. No se declara capacidad de miles de escritores concurrentes ni sincronización distribuida.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
