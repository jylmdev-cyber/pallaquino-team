# Plantilla: API y CLI

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/development/API_DOCUMENTATION.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: La interfaz pública es CLI, no servidor REST. Flags globales: --root, --output y --verbose antes del comando. Cada subcomando tiene --help. Wrappers aceptan flags globales en ambas posiciones. Funciones Python son internas y pueden evolucionar con la versión. OpenAPI en templates/api es una base para futuros proyectos, no una API implementada. Para capacidades ver README y manual.
