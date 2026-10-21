---
name: environment-setup
description: Aplicar environment setup cuando el encargo requiera so y manifiestos.
---

# Environment Setup

## Entradas y parámetros

SO y manifiestos. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Inspeccionar versiones disponibles y declarar requisitos. Aislar dependencias, documentar diferencias entre plataformas y no copiar credenciales.

## Ejemplo

python -m venv .venv; ejecutar kit desde checkout.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Doctor y pruebas ejecutables en entorno limpio. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
