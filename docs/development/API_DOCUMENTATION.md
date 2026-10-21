# API y CLI

La interfaz pública es CLI, no servidor REST. Flags globales: --root, --output y --verbose antes del comando. Cada subcomando tiene --help. Wrappers aceptan flags globales en ambas posiciones. Funciones Python son internas y pueden evolucionar con la versión. OpenAPI en templates/api es una base para futuros proyectos, no una API implementada. Para capacidades ver README y manual.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
