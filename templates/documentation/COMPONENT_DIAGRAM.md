# Plantilla: Componentes

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/architecture/COMPONENT_DIAGRAM.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: ```mermaid
flowchart TD
  CLI[kit.py y tools] --> Dispatch[uasek.cli]
  Dispatch --> Memory[PROJECT MEMORY y tareas]
  Dispatch --> Ops[Operaciones locales]
  Dispatch --> Providers[Adaptadores]
  Memory --> Files[(JSON y Markdown)]
  Ops --> Reports[Reportes y pruebas]
  Providers --> Manual[Handoff manual]
  Providers --> Ollama[HTTP loopback]
```
