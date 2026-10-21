---
name: threat-modeling
description: Aplicar threat modeling cuando el encargo requiera flujos, usuarios y despliegue.
---

# Threat Modeling

## Entradas y parámetros

Flujos, usuarios y despliegue. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Identificar activos y fronteras; enumerar abuso por actor. Asignar mitigación verificable y riesgo residual con propietario.

## Ejemplo

Un documento externo intenta inducir al agente a revelar variables de entorno.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Cada amenaza relevante tiene control y prueba o riesgo aceptado. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
