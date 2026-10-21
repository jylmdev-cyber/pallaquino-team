# Reporte final de validación — UASEK 1.1.0

Fecha: 2026-10-21. Entorno: Windows, Python 3.12.10. Memoria local compatible con schema 1; nuevo contexto de intercambio v1. La entrega 1.0 y su [reporte original](VALIDATION_REPORT_1.0.0.md) se conservan.

## Resultado comprobado

| Verificación | Resultado | Evidencia |
|---|---|---|
| Suite completa | 72 pruebas: 71 pasaron, 1 omitida por permisos de symlink en Windows | [tests-1.1.0](evidence/tests-1.1.0.json) |
| Código extraído del ZIP | Misma suite y misma huella de fuentes que el checkout; dos checkpoints íntegros | [extracted-zip-1.1.0](evidence/extracted-zip-1.1.0.json) |
| Wheel 1.1 instalado en venv aislado | Nueve operaciones comprobadas: inicializar, planificar, reusar plan, verificar checkpoint, exportar, preparar receptor, cambiar proveedor, importar y consultar estado | [installed-wheel-1.1.0](evidence/installed-wheel-1.1.0.json) |
| Skills | 31 válidas estructuralmente tras actualizar instrucciones de continuidad | [skills-1.1.0](evidence/skills-1.1.0.json) |
| Escaneo heurístico | Sin hallazgos altos; se repite antes de empaquetar | [security-1.1.0](evidence/security-1.1.0.json) |
| Auditoría Git completa autorizada | No pudo ejecutarse: la carpeta no pertenece a un repositorio Git. No se creó uno ni se declara una auditoría exitosa | [git-audit-1.1.0](evidence/git-audit-1.1.0.json) |
| Base anterior recuperable | Checkpoint reconstruido desde los bytes del ZIP original 1.0, preservando su procedencia y reporte previo de pruebas | [baseline-1.1.0](evidence/baseline-1.1.0.json) |

Resumen e identificadores de checkpoints: [summary-1.1.0](evidence/summary-1.1.0.json).

## Tres mejoras implementadas

**Memoria independiente del modelo.** Exportación JSON versionada y checksum canónico; importación validada antes de escribir; conservación del proveedor local receptor; rechazo de versiones desconocidas, corrupción y rutas fuera de alcance. Se informa evidencia no disponible localmente. Las instrucciones de proveedores se generan en archivos separados del estado universal. No se depende de prompts internos iguales entre aplicaciones. [Formato y comandos](../continuity/CONTEXT_FORMAT.md).

**Checkpoints recuperables.** Captura de fuentes de texto seleccionadas, memoria, decisiones, expectativa y pruebas disponibles. Distingue pruebas frescas, obsoletas o ausentes. Verificación de metadatos, archivo ZIP y hashes; rechazo de snapshots alterados y rutas adversas. Recuperación real en carpeta nueva sin tocar el proyecto actual. Checkpoint automático antes de aplicar un plan o sustituir memoria por importación. Para editar fuera del kit, el responsable debe crearlo antes del cambio. [Guía](../continuity/CHECKPOINTS.md).

**Orquestación adaptable.** Reglas locales y versionadas seleccionan roles según tipo, señales y archivos, con presupuesto predeterminado de cuatro. Documentación sencilla usa un solo perfil. Se explican selecciones y roles diferidos; no se permite aplicar un presupuesto que omita controles QA/seguridad requeridos. Planes persistentes e idempotentes, tareas con dependencias y ejecución secuencial por defecto. La planificación no llama modelos ni ejecuta sus respuestas. [Guía](../workflows/ADAPTIVE_ORCHESTRATION.md).

## Cobertura y límites

Las nuevas pruebas reproducen transferencia de decisiones/tareas entre proveedores distintos, pérdida o alteración del contexto, preservación de requisitos existentes, evidencia ausente, recuperación de código anterior tras romper el actual, corrupción de checkpoints, traversal ZIP, dry-run sin escrituras y planes sin duplicación.

El contexto no copia código ni prueba la veracidad de hechos importados. Un digest detecta alteraciones accidentales, no autentica al remitente. Los checkpoints son de fuentes de texto: omiten secretos detectados, binarios, bases y archivos grandes; consultar siempre `omitted`. La recuperación requiere ejecutar pruebas de nuevo en el entorno destino.

La selección de roles es por reglas explicables, no comprensión semántica completa. Los criterios del plan requieren revisión según el negocio antes de implementar funciones complejas. No se lanzan agentes autónomos ni se concede autorización por planear una tarea. No se interceptan cambios arbitrarios de IDEs.

No se ejecutaron modelos reales, API cloud, CI remota ni Linux/macOS. Se mantienen transferencias manuales cloud y adaptador Ollama local de texto. Las pruebas de transporte de modelos usan fixtures. Las consultas reales PyPI/OSV de 1.0 permanecen documentadas en el reporte anterior; no se repitieron al cambiar funcionalidades locales.

El ZIP incluye ambas bases recuperables y un manifiesto de archivos. La validación completa de la copia extraída se realizó antes de añadir este informe final; esos cambios finales son documentación, no fuentes/configuración. El cierre verifica otra vez la huella de código, los hashes del ZIP y los checkpoints. El checksum del comprimido se entrega al lado en `.zip.sha256`.

## Reproducir

```console
python kit.py test
python kit.py context export
python kit.py checkpoint list
python kit.py orchestrate --request "Documentar README"
```

Para crear, importar o recuperar con dry-run y parámetros completos, consultar las guías enlazadas y el [manual](../user-manual/MANUAL.md).
