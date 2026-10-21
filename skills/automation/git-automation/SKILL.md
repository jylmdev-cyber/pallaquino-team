---
name: git-automation
description: Aplicar git automation cuando el encargo requiera intención y ruta del repositorio.
---

# Git Automation

## Entradas y parámetros

Intención y ruta del repositorio. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Pedir opción de auditoría completa, rápida, rechazar o sin Git. Solo pasar --authorize tras respuesta afirmativa. No ejecutar reset, force push ni limpieza automática.

## Ejemplo

python kit.py audit --authorize --full

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Reporte local de solo lectura con límites; sin cambios Git. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
