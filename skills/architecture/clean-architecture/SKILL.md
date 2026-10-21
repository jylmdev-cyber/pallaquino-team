---
name: clean-architecture
description: Aplicar clean architecture cuando el encargo requiera código y motivos de cambio.
---

# Clean Architecture

## Entradas y parámetros

Código y motivos de cambio. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Identificar reglas de dominio y aislar dependencias que cambian. No añadir capas sin necesidad; probar reglas sin infraestructura.

## Ejemplo

Extraer cálculo de precio para probar sin base de datos.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Dominio probado sin servicios externos; interfaces justificadas. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
