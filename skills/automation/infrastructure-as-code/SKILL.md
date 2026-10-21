---
name: infrastructure-as-code
description: Aplicar infrastructure as code cuando el encargo requiera entorno, presupuesto y proveedor.
---

# Infrastructure As Code

## Entradas y parámetros

Entorno, presupuesto y proveedor. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Describir recursos, costos y estado; generar plan revisable. Evitar aplicar contra producción sin aprobación explícita del plan.

## Ejemplo

Validar plan para nuevo bucket con acceso privado.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Plan revisado y recuperación de estado definida. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
