---
name: model-evaluation
description: Aplicar model evaluation cuando el encargo requiera casos representativos y criterios.
---

# Model Evaluation

## Entradas y parámetros

Casos representativos y criterios. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Separar fixtures de pruebas con modelo real. Definir casos y rúbrica; medir exactitud, seguridad, latencia y costo en entorno autorizado.

## Ejemplo

Mock HTTP valida payload; prueba real requiere servidor/modelo disponible.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Reporte distingue pruebas simuladas, reales y no ejecutadas. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
