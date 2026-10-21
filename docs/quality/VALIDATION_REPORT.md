# Reporte de validación — UASEK 2.0.0

Fecha: 2026-10-21. Entorno ejecutado: Windows, Python 3.12.10. Núcleo sin dependencias externas de ejecución. Memoria clásica schema 1; API/estado de plataforma v1; ambos contextos universales v1. Se conservan los reportes [1.0](VALIDATION_REPORT_1.0.0.md) y [1.1](VALIDATION_REPORT_1.1.0.md).

| Verificación ejecutada | Resultado | Evidencia |
|---|---|---|
| Suite completa mediante CLI | 120 pruebas, 119 aprobadas y 1 omitida por privilegios de symlink en Windows | [tests](evidence/tests-2.0.0.json) |
| Demostración desde fuentes | Dos procesos independientes, máximo paralelo 2, ambos integrados como done tras gates y aprobaciones | [demo](evidence/demo-2.0.0.json) |
| Wheel 2.0 instalado en venv aislado | Importación desde site-packages, API v1, misma demo paralela, CLI de estado y cadena de auditoría verificada | [wheel](evidence/installed-wheel-2.0.0.json) |
| ZIP de ensayo extraído | Hashes de todos los archivos correctos, misma huella de fuentes, 120 pruebas aprobadas con la misma omisión, tres checkpoints íntegros | [ZIP extraído](evidence/extracted-zip-2.0.0.json) |
| Enlaces Markdown locales | 206 referencias verificadas antes del reporte final; se vuelven a comprobar en el ZIP final | [ZIP extraído](evidence/extracted-zip-2.0.0.json) |
| Escaneo heurístico | Sin hallazgos; los archivos ZIP internos no se escanean como texto y se verifican por sus manifests de checkpoint | [seguridad](evidence/security-2.0.0.json) |
| Auditoría Git completa autorizada previa al cambio | main limpia y sincronizada con origin/main; commit inicial presente | [auditoría](evidence/git-audit-before-eip.json) |

## Plataforma implementada y cobertura

La [guía EIP](../platform/PLATFORM.md) relaciona las capacidades A–O con módulos, formatos, comandos y límites. Incluye PROJECT BRAIN, búsqueda léxica con procedencia, transferencia sin importar autorizaciones, mapa Python AST y adaptador léxico JS/TS, coordinación con dependencias y reservas de archivos, presupuestos, cuatro niveles de autonomía, permisos acotados de uso único, quality gates obligatorios, revisión e integración, recuperación, modelos declarados, extensiones revisadas, registro multiproyecto, trazabilidad y HTML local opcional.

Las 48 pruebas nuevas comprueban procesos realmente solapados y serialización de archivos compartidos; dependencias y presupuestos; aprobación ligada a bytes de entradas y raíz local; cambios entre reserva y ejecución; rechazo de candidatos alterados; gates de regresión y cierre de tareas; permisos críticos incluso en autonomía máxima; reintentos limitados y reparación declarada; timeout; leases y resultados tardíos; fallo parcial de integración simulado mediante error real de escritura y restauración en carpeta nueva; aislamiento de proyectos y clones; corrupción de auditoría; documentación desactualizada; lecciones con evidencia; transferencia neutral; contratos y versiones; adaptador de proceso con permisos; rechazo seguro sin Docker; inferencia local mediante fixtures. Se conservan las 72 pruebas de compatibilidad del núcleo anterior.

La demo autoriza únicamente scripts locales conocidos. No conecta modelos, cambia políticas ni despliega un producto. Los módulos frontend/backend de la demo son fixtures de texto para reproducir coordinación, revisión y regresión.

## Límites efectivamente pendientes

No se ejecutaron Docker real, modelos reales, APIs cloud, despliegues externos ni CI Linux/macOS. El pipeline versionado permite ejecutar la suite en esos sistemas, pero su configuración no es evidencia de ejecución. Los tests de modelos y producción usan fixtures. Otros lenguajes requieren sus herramientas específicas mediante conectores revisados; no se declara análisis semántico completo fuera de Python.

El ejecutor nativo exige código revisado y no es un sandbox para código hostil. El contrato Docker requiere imagen aprobada por digest, ausencia de red y límites; falla sin runtime y nunca recurre al ejecutor nativo. Debe validarse con el daemon real antes de utilizar código no confiable. Las aprobaciones identifican revisores declarados localmente; no son autenticación corporativa. El encadenamiento de hashes detecta corrupción, no autentica administradores. El control de aplicación no impide cambios directos por el propietario del sistema de archivos.

El catálogo de modelos usa disponibilidad, costos y latencia declarados, no precios o facturación en vivo. Las APIs cloud siguen usando transferencia manual o adaptadores externos por implementar/revisar. Los conectores permiten comandos reproducibles de desarrollo, pruebas, staging y producción sujetos a permisos; no se provisiona infraestructura cloud. Los checkpoints son respaldos de fuentes seleccionadas, no backups de bases de datos o producción. La integración es atómica por archivo; un fallo entre archivos exige revisar journal y checkpoint.

## Reproducir

```console
python kit.py doctor
python kit.py test
python examples/platform/demo.py --destination ../demo-eip --approve-demo
python kit.py checkpoint list
```

La plataforma es optativa por proyecto. Inicializar con `platform init` aplica la política supervisada, también a los comandos anteriores; consultar `--policy-preview` y la guía de aprobaciones. El código fuente del kit mantiene esta activación explícita para conservar el flujo de instalación previo.

La distribución final contiene un checkpoint adicional de cierre, manifiesto SHA-256 por archivo y checksum externo del ZIP. Se comprueban otra vez hashes, enlaces y huella de fuentes después de cerrar documentación/memoria; estas últimas escrituras no modifican el código probado. La copia de ensayo conserva su evidencia separada.
