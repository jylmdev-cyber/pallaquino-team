# Casos de prueba

Desde 1.1, `tests/test_continuity.py` añade 21 casos de transferencia neutral, checksum y versiones, validación antes de importar, preservación del proveedor local, memoria previa protegida por checkpoint, evidencia ausente, captura de pruebas frescas/obsoletas, recuperación real, snapshots alterados, rutas adversas, dry-run, selección de roles por alcance, presupuesto, planes idempotentes y aplicación sin llamadas a modelos.

TC-01 init rechaza sobrescritura; TC-02 traversal rechazado; TC-03 dependencia bloquea ejecución; TC-04 cierre exige evidencia; TC-05 lock rechaza segundo escritor; TC-06 contexto conserva tareas; TC-07 red fallida es error; TC-08 copia excluye secretos y verifica SHA; TC-09 cero tests falla; TC-10 cloud API ausente se rechaza; TC-11 contrato de agente inválido falla; TC-12 fuente modificada invalida release. Implementación y casos adicionales en tests/test_core.py.

Ver [manual de usuario](../user-manual/MANUAL.md) y [manual técnico](../technical-manual/MANUAL.md).
