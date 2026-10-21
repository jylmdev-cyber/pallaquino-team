---
name: refactoring
description: Aplicar refactoring cuando el encargo requiera código y contratos actuales.
---

# Refactoring

## Entradas y parámetros

Código y contratos actuales. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Crear una caracterización del comportamiento que debe conservarse. Cambiar una frontera a la vez y comparar resultados; registrar incompatibilidades.

## Ejemplo

Extraer parser sin cambiar errores públicos.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Pruebas de caracterización pasan y cambios de comportamiento explicados. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
