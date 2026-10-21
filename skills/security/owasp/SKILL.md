---
name: owasp
description: Aplicar owasp cuando el encargo requiera superficie web/api.
---

# Owasp

## Entradas y parámetros

Superficie web/API. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Seleccionar controles aplicables según superficie y consultar fuentes oficiales vigentes. No tratar una lista como certificación; verificar controles de acceso por objeto.

## Ejemplo

Cambiar order_id no permite acceder a pedidos de otro tenant.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Controles probados con evidencia y cobertura delimitada. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
