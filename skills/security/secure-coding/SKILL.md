---
name: secure-coding
description: Aplicar secure coding cuando el encargo requiera flujo y activos.
---

# Secure Coding

## Entradas y parámetros

Flujo y activos. Usar la ruta del proyecto, alcance y criterios del encargo. Marcar datos faltantes como pendientes; no inventarlos.

## Procedimiento

Seguir entrada no confiable hasta sus efectos. Validar fronteras de rutas, usar parámetros SQL y procesos sin shell; probar rechazo de entradas adversas.

## Ejemplo

safe_path rechaza ../fuera antes de escribir.

## Dependencias

Contrato del agente asignado y PROJECT MEMORY. Para comandos del kit: Python 3.11+ y checkout de UASEK; los comandos de red o Git requieren esas capacidades cuando se indiquen.

## Finalización verificable

Casos adversos no cruzan fronteras ni filtran secretos. Registrar archivos y resultado de comprobaciones, incluidos los fallos o pruebas no ejecutadas.
