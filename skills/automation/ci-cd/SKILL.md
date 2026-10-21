---
name: ci-cd
description: Aplicar ci cd cuando el encargo requiera comandos de build/test.
---

# Ci Cd

## Entradas y parámetros

Comandos de build/test. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Separar validación de publicación. Aplicar permisos mínimos, no exponer secretos a contribuciones no confiables y fijar dependencias del pipeline.

## Ejemplo

Validación en matriz Windows/Linux/macOS, despliegue manual aparte.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Pipeline falla ante pruebas fallidas y no publica sin autorización. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
