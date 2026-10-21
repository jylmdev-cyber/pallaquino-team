---
name: security-testing
description: Aplicar security testing cuando el encargo requiera modelo de amenazas y entorno aislado.
---

# Security Testing

## Entradas y parámetros

Modelo de amenazas y entorno aislado. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Definir alcance y autorización del entorno. Empezar con casos locales de abuso; no lanzar carga ni explotación sobre servicios externos sin permiso.

## Ejemplo

Probar traversal en carpeta temporal.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Cada hallazgo tiene reproducción sin datos sensibles. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
