---
name: secrets-detection
description: Aplicar secrets detection cuando el encargo requiera repositorio autorizado.
---

# Secrets Detection

## Entradas y parámetros

Repositorio autorizado. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Ejecutar escaneo sin imprimir coincidencias. Si un secreto es real, coordinar rotación y revisión del historial; no reescribir Git automáticamente.

## Ejemplo

python kit.py security

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Hallazgos sin valores; falsos positivos justificados y cobertura indicada. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
