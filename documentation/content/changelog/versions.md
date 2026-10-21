# Versiones y estado documental

El portal UDP edición 1 documenta **PALLAQUINO TEAM 2.0.0**, incluido su núcleo UASEK y Engineering Intelligence Platform. Cambiar el nombre de presentación no cambia los identificadores de instalación, comandos ni formatos.

## Historial disponible

| Versión del software | Alcance | Evidencia histórica |
|---|---|---|
| 1.0.0 | Núcleo CLI, memoria, perfiles, skills y plantillas | [Reporte 1.0](/generated/reference/docs/quality/VALIDATION_REPORT_1.0.0.html) |
| 1.1.0 | Contexto portable, checkpoints y orquestación adaptable | [Reporte 1.1](/generated/reference/docs/quality/VALIDATION_REPORT_1.1.0.html) |
| 2.0.0 | EIP: gobierno, ejecución paralela, gates y extensiones | [Reporte 2.0](/generated/reference/docs/quality/VALIDATION_REPORT.html) |
| UDP edición 1 | Portal estático y automatización documental | [Validación del portal](/quality/validation.html) |

Los reportes anteriores son evidencia fechada y se conservan; no equivalen a validación del código modificado después. Sus archivos internos de ejecución no se publican en el portal. Las distribuciones y checkpoints mantienen su nombre y hash originales.

## Compatibilidad

La memoria clásica schema 1 y los contextos v1 se mantienen. La documentación activa deriva de los archivos actuales; las fichas generadas no simulan versiones anteriores de APIs. Para consultar una implementación histórica, utiliza el commit o distribución correspondiente y su reporte.

## Política de archivo

No sobrescribir reportes históricos. Si se publica otra versión, conserva fuentes y evidencia de la anterior en una ruta con versión o referencia al commit, actualiza el índice y rotula cualquier contenido obsoleto. La CI no crea snapshots de versiones ficticias ni descarga versiones anteriores durante el build.

[Changelog del software](/generated/reference/docs/continuity/CHANGELOG.html) · [Repositorio](https://github.com/jylmdev-cyber/pallaquino-team)
