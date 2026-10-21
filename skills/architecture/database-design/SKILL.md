---
name: database-design
description: Aplicar database design cuando el encargo requiera entidades, volúmenes y consultas.
---

# Database Design

## Entradas y parámetros

Entidades, volúmenes y consultas. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Modelar claves y restricciones antes de índices. Diseñar transacciones según invariantes y justificar índices con consultas medidas.

## Ejemplo

UNIQUE(tenant_id, external_id) evita duplicados entre reintentos.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Integridad y aislamiento entre empresas comprobados. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
