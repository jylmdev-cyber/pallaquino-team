---
name: provider-switching
description: Aplicar provider switching cuando el encargo requiera proveedor y modo.
---

# Provider Switching

La transferencia se basa en `project-memory/PROJECT_CONTEXT.json`, independiente del modelo. `provider switch` genera instrucciones de adaptación separadas en `ai/handoff/PROVEEDOR.md`; no insertar prompts internos en el estado universal. Ver [contrato de intercambio](../../../docs/continuity/CONTEXT_FORMAT.md).

## Entradas y parámetros

Proveedor y modo. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Consultar capacidades y diferenciar aplicación de API. Exportar memoria, seleccionar destino y entregar manualmente si no hay adaptador nativo.

## Ejemplo

python kit.py provider switch --provider gemini

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Decisiones y pendientes conservados; modo API no implementado se rechaza. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
