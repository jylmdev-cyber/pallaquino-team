---
name: code-review
description: Aplicar code review cuando el encargo requiera diff, intención y pruebas.
---

# Code Review

## Entradas y parámetros

Diff, intención y pruebas. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Seguir datos y permisos por el flujo cambiado. Revisar regresiones y errores antes del estilo; citar archivo y línea con caso reproducible.

## Ejemplo

Una consulta por id sin tenant permite leer otra empresa.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Hallazgos accionables con impacto y evidencia. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
