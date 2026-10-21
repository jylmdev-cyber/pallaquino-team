# Reporte final de validación — UASEK 1.0.0

Fecha: 2026-10-21. Entorno local: Windows, Python 3.12.10, Git 2.55.0.windows.5. La validación usa proyectos temporales propios; no se ejecutó auditoría de un repositorio del usuario.

## Resultado ejecutado

| Verificación | Resultado | Evidencia |
|---|---|---|
| Suite de comportamiento, fronteras y flujo completo CLI | 51 pruebas: 50 pasaron, 1 omitida; salida 0 | [tests.json](evidence/tests.json) |
| Suite desde ZIP extraído | Mismo resultado y misma huella de fuentes/configuración que el checkout | [extracted-zip.json](evidence/extracted-zip.json) |
| Construcción e instalación del wheel en venv aislado | Correcta; doctor, catálogo, agentes, proveedores e init con plantilla comprobados | [installed-wheel.json](evidence/installed-wheel.json) |
| Skills | 31 pasaron el validador estructural de skill-creator | [skills.json](evidence/skills.json) |
| Referencias internas Markdown | Enlaces existentes comprobados; el informe final se añadió después de esa captura | [links.json](evidence/links.json) |
| Escaneo heurístico de fuentes | Sin hallazgos en la captura; empaquetado repite el control antes de generar cada ZIP | [security.json](evidence/security.json) |
| Dependencias locales del kit | Sin dependencias runtime declaradas; no equivale a auditoría del Python/SO/build | [dependency-local.json](evidence/dependency-local.json) |
| Consulta real PyPI | Metadatos obtenidos desde registro oficial, con fecha y fuente | [pypi-online.json](evidence/pypi-online.json) |
| Consulta real OSV sobre fixture PyYAML 5.3 | Vulnerabilidades detectadas, código 1 esperado; el paquete vulnerable no se instaló | [osv-online.json](evidence/osv-online.json) |

Las pruebas cubren los 16 puntos de entrada, no sobrescritura, dry-run, incorporación de memoria a proyectos existentes, dependencias entre tareas, evidencia de cierre, locks, memoria corrupta, ciclos introducidos manualmente, redacción, contratos de agentes, fallos de red, cobertura incompleta, respaldo y hashes, documentos humanos conservados, pruebas vacías, release con código cambiado y menú sin escrituras.

La prueba de auditoría Git verifica estado e índice sin cambios en un repositorio temporal. La auditoría desactiva hooks, fsmonitor, firmas, diffs externos y escrituras opcionales. La prueba de enlace simbólico se omitió porque Windows negó crear el enlace sin privilegios; la validación de traversal y las restantes fronteras sí se ejecutaron.

El empaquetador añade `PACKAGE_MANIFEST.json` con SHA-256 de cada archivo. La distribución fuente extraída se probó completa. Los archivos añadidos al cierre son documentación y memoria; la huella comprobada excluye esos datos y el propio manifiesto de empaquetado. El checksum del ZIP definitivo se entrega en un archivo hermano `.zip.sha256`.

## Implementado

- CLI central y 16 wrappers reales con ayuda, validación y códigos de salida.
- 21 contratos de agentes y encargos con contrato de resultado portable incluido.
- 31 skills con entradas, procedimientos, ejemplos y finalización verificable.
- 30 referencias sectoriales con negocio, reglas, modelo, diagramas, endpoints ilustrativos, seguridad y plan de pruebas.
- PROJECT MEMORY, DAG de tareas, revisión de resultados y exportación de diez secciones.
- Transferencia manual para proveedores y aplicaciones; cliente nativo local Ollama de texto.
- Inventario, auditoría Git autorizada, escaneo heurístico, consultas PyPI/npm y OSV acotadas.
- Documentación derivada que conserva ediciones humanas, respaldo de fuentes y preparación local de release.
- Manuales, guías técnicas, plantillas, pipeline propuesto y empaquetador con manifiesto.

## Fixtures y comprobaciones pendientes

Los tests de Ollama usan mocks y un servidor HTTP local fixture: prueban transporte y contrato, no un modelo real ni la calidad de su salida. Las llamadas reales efectuadas fueron PyPI y OSV. La validación estructural de skills no evalúa el comportamiento de un asistente.

No se ejecutaron Linux/macOS ni CI remota; la matriz incluida permite hacerlo después. No se probaron servicios cloud, despliegues, aplicaciones comerciales ni cumplimiento normativo. El pipeline usa referencias de acciones fijadas y verificadas contra sus etiquetas oficiales; su ejecución remota no se afirma.

## Límites deliberados

Los perfiles no son 21 procesos autónomos de IA. La ejecución se realiza con asistentes/personas autorizados y el cierre exige revisión humana de criterios; la existencia de archivos no demuestra calidad semántica. Las API cloud no están implementadas: se entrega handoff manual para OpenAI/ChatGPT, Claude, Gemini, Copilot, Cursor, Windsurf, OpenRouter y otros.

El runner incluido es unittest. Otros ecosistemas necesitan sus runners externos. Dependencias: versiones exactas PyPI y package-lock npm v2/v3; no resuelve todos los locks ni dependencias transitivas de Python. El escáner es heurístico y no garantiza ausencia de secretos. Revisar contexto antes de compartir. Los respaldos son de fuentes de texto, omiten secretos detectados, binarios y bases de datos, y no sustituyen una solución cifrada de producción.

JSON y vistas Markdown no forman una transacción conjunta. No hay coordinación entre máquinas, despliegue, publicación, restauración destructiva ni migrador entre futuras versiones de memoria. Estas extensiones están en [ROADMAP](../continuity/ROADMAP.md), separadas de las capacidades entregadas.

## Reproducir

```console
python kit.py doctor
python kit.py test
python kit.py security
python kit.py dependency
python scripts/package_kit.py --destination ../nuevo-kit.zip --dry-run
```

Los resultados online se consultan de nuevo solo con `--online`; pueden variar con el registro y los avisos publicados. Para conocer uso y parámetros: [manual de usuario](../user-manual/MANUAL.md).
