---
name: requirements-engineering
description: Aplicar requirements engineering cuando el encargo requiera actor, problema, reglas conocidas.
---

# Requirements Engineering

## Entradas y parámetros

Actor, problema, reglas conocidas. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Separar hechos, supuestos y preguntas. Numerar RF/RNF y vincularlos a criterios observables; pedir solo información que cambie alcance o aceptación.

## Ejemplo

Dado un pedido duplicado, cuando se reintenta el pago, entonces existe un solo cargo.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Cada requisito tiene fuente, prioridad y criterio medible. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
