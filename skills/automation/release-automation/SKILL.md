---
name: release-automation
description: Aplicar release automation cuando el encargo requiera versión y evidencia.
---

# Release Automation

## Entradas y parámetros

Versión y evidencia. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Comprobar versión, tareas y reporte de pruebas reciente. Preparar notas y paquete revisable; no confundir preparación con publicación.

## Ejemplo

python kit.py release --version 1.0.0 --dry-run

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Pruebas y escaneo revisados; no se publica automáticamente. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
