---
name: dependency-auditing
description: Aplicar dependency auditing cuando el encargo requiera requirements exactos o lock npm.
---

# Dependency Auditing

## Entradas y parámetros

requirements exactos o lock npm. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Usar versiones resueltas y distinguir desconocido de limpio. Solicitar --online antes de enviar metadatos a OSV; no instalar ni actualizar automáticamente.

## Ejemplo

python kit.py dependency --online

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Informe separa vulnerabilidades, entradas no resueltas y errores de red. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
