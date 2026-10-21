---
name: database-migrations
description: Aplicar database migrations cuando el encargo requiera esquema origen/destino y respaldo.
---

# Database Migrations

## Entradas y parámetros

Esquema origen/destino y respaldo. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Usar expandir/migrar/contraer cuando haya clientes coexistentes. Ensayar copia y reconciliar conteos e integridad antes del corte.

## Ejemplo

Añadir campo nullable, rellenar, actualizar lectores, imponer NOT NULL.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Ensayo y reversión o reparación hacia adelante documentados. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
