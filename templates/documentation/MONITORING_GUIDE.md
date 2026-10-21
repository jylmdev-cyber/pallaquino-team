# Plantilla: Observabilidad

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/operations/MONITORING_GUIDE.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: Mutaciones registran at, command y outcome en .uasek/events.jsonl. El contenido de prompts no se registra. stdout entrega JSON redactado y códigos de salida para integración. test conserva last-test.json con comando, salida acotada, resultado y huella. No hay servicio daemon, métricas en red ni alertas automáticas.
