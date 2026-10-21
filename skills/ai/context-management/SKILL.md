---
name: context-management
description: Aplicar context management cuando el encargo requiera estado, decisiones y próximas acciones.
---

# Context Management

Usar `context export` para generar contexto universal JSON v1 además del Markdown. Conservar hechos y decisiones fuera de instrucciones de proveedores; `context import --file ...` mantiene el proveedor local y valida integridad. Antes de reemplazar memoria existente se exige `--replace-memory` y se crea checkpoint. Ver [formato](../../../docs/continuity/CONTEXT_FORMAT.md).

## Entradas y parámetros

Estado, decisiones y próximas acciones. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Guardar hechos y decisiones fuera de conversación. Usar state.json como fuente; derivar Markdown con herramientas y exportar sin código ni secretos.

## Ejemplo

python tools/context_manager.py export

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Otro asistente identifica tarea siguiente y evidencia sin rehacer descubrimiento. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
