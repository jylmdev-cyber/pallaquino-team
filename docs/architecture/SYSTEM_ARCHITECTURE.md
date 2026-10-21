# Arquitectura

CLI → despacho → memoria/operaciones/proveedores → archivos locales o HTTP explícito. Cada operación recibe root; recursos del kit se resuelven aparte del proyecto. Separar estado del proyecto de recursos inmutables evita imponer stack de aplicación. Las decisiones de concurrencia y cobertura están en el manual técnico.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
