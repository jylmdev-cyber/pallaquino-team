# Plantilla: Arquitectura

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/architecture/SYSTEM_ARCHITECTURE.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: CLI → despacho → memoria/operaciones/proveedores → archivos locales o HTTP explícito. Cada operación recibe root; recursos del kit se resuelven aparte del proyecto. Separar estado del proyecto de recursos inmutables evita imponer stack de aplicación. Las decisiones de concurrencia y cobertura están en el manual técnico.
