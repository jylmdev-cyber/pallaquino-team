---
name: backup-automation
description: Aplicar backup automation cuando el encargo requiera objetivos de recuperación.
---

# Backup Automation

## Entradas y parámetros

Objetivos de recuperación. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Definir qué se respalda y qué se excluye. Crear copia exclusiva, verificar hash y ensayar restauración en destino nuevo; bases y secretos requieren solución cifrada aparte.

## Ejemplo

python kit.py backup --destination ../source-backup.zip

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Manifiesto verificado y límites de recuperación explícitos. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
