---
name: software-testing
description: Aplicar software testing cuando el encargo requiera criterios de aceptación.
---

# Software Testing

## Entradas y parámetros

Criterios de aceptación. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Elegir casos por riesgo y frontera. Cubrir error, vacío, repetición y concurrencia cuando afecten invariantes. Registrar comando y entorno.

## Ejemplo

Segundo reintento de pago no duplica movimiento.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Pruebas fallan ante regresión relevante y pasan con corrección. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
