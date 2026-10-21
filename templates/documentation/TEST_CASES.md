# Plantilla: Casos de prueba

Propósito y ejemplo aplicado al kit: [documento de referencia](../../docs/quality/TEST_CASES.md).

Al adaptarlo: describir únicamente hechos confirmados de su proyecto, vincular requisitos y tareas, indicar responsable y fecha, y aportar evidencia reproducible. Si falta una decisión, declarar la pregunta y quién la resolverá. No copiar las capacidades de UASEK como si pertenecieran a su aplicación.

Guía de contenido para este documento: TC-01 init rechaza sobrescritura; TC-02 traversal rechazado; TC-03 dependencia bloquea ejecución; TC-04 cierre exige evidencia; TC-05 lock rechaza segundo escritor; TC-06 contexto conserva tareas; TC-07 red fallida es error; TC-08 copia excluye secretos y verifica SHA; TC-09 cero tests falla; TC-10 cloud API ausente se rechaza; TC-11 contrato de agente inválido falla; TC-12 fuente modificada invalida release. Implementación y casos adicionales en tests/test_core.py.
