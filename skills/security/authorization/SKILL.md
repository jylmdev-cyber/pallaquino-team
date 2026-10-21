---
name: authorization
description: Aplicar authorization cuando el encargo requiera roles, recursos y tenants.
---

# Authorization

## Entradas y parámetros

Roles, recursos y tenants. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Denegar por defecto y aplicar permisos del lado servidor, por objeto y empresa. Probar matriz rol/recurso/acción.

## Ejemplo

Un operador de A no consulta facturas de B.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Accesos prohibidos fallan incluso con IDs válidos. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
