---
name: agent-orchestration
description: Aplicar agent orchestration cuando el encargo requiera solicitud y contratos.
---

# Agent Orchestration

En UASEK 1.1, usar `orchestrate --request "..."` para obtener selección explicada y limitada de roles. Revisar los roles diferidos y el alcance; `--apply` crea un checkpoint y tareas secuenciales sin invocar modelos, y repetirlo no duplica trabajo. Ajustar criterios antes de implementar funcionalidades complejas. Ver [guía](../../../docs/workflows/ADAPTIVE_ORCHESTRATION.md).

## Entradas y parámetros

Solicitud y contratos. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Crear tareas pequeñas con responsable, criterio y dependencias hacia tareas existentes. Usar task ready y agent brief; revisar resultados antes de cerrar.

## Ejemplo

Requisitos → arquitectura → implementación → QA.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

No hay tareas activadas con dependencias incompletas; cierre tiene evidencia. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
