---
name: authentication
description: Aplicar authentication cuando el encargo requiera modelo de identidad.
---

# Authentication

## Entradas y parámetros

Modelo de identidad. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Definir identidad, ciclo de sesión y revocación; no construir criptografía propia. Comprobar expiración, fijación y recuperación de cuenta.

## Ejemplo

Una sesión revocada no puede renovar acceso.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Casos de expiración y revocación probados. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
