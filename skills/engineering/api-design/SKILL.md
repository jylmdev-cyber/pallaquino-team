---
name: api-design
description: Aplicar api design cuando el encargo requiera consumidores y casos de uso.
---

# Api Design

## Entradas y parámetros

Consumidores y casos de uso. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Precisar esquemas, errores, permisos, versionado, paginación e idempotencia. Verificar consumidores antes de romper contrato.

## Ejemplo

POST /orders con clave de idempotencia devuelve el resultado original en reintento.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Contrato y pruebas cubren éxito, error y duplicado. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
