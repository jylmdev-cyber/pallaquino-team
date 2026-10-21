# Manual de usuario UASEK

## Capacidades incorporadas en 1.1

Consulte [contexto universal e importación](../continuity/CONTEXT_FORMAT.md), [checkpoints y recuperación](../continuity/CHECKPOINTS.md) y [orquestación adaptable](../workflows/ADAPTIVE_ORCHESTRATION.md) para comandos completos. `context export` conserva el handoff anterior y añade JSON universal sin configuración local del proveedor. `orchestrate --apply` selecciona roles, crea un checkpoint y materializa tareas sin invocar modelos. `checkpoint restore` recupera en una carpeta nueva para revisar e integrar.

## 1. Qué es

UASEK proporciona coordinación, estado durable y automatizaciones locales para trabajo con asistentes de IA. El producto resultante de cada proyecto sigue requiriendo requisitos, implementación y validación específicas.

## 2. Cómo funciona

`kit.py` delega a `uasek/cli.py`. Los perfiles de `agents/` remiten a contratos canónicos; `skills/` contiene procedimientos. `project-memory/state.json` es la fuente del estado, las vistas Markdown se derivan al guardar. Los agentes intercambian encargos y resultados en archivos.

## 3. Requisitos

Python 3.11 o posterior. Git para auditorías. Internet solo para consultas seleccionadas con `--online`. Ollama y un modelo ya instalado solo si se usa inferencia local. El núcleo no necesita claves ni instala dependencias del proyecto analizado.

## 4. Instalación Windows, Linux y macOS

Extraer el ZIP. En Windows: `cd UNIVERSAL-AI-SOFTWARE-KIT` y `python kit.py doctor` (o `py -3 kit.py doctor`). En Linux/macOS: `cd UNIVERSAL-AI-SOFTWARE-KIT` y `python3 kit.py doctor`. En los ejemplos siguientes, sustituya `python` por su ejecutable.

Opcional: `python -m venv .venv`. Windows activa con `.venv\Scripts\Activate.ps1`; Linux/macOS con `source .venv/bin/activate`. Para instalar el comando `uasek`: `python -m pip install .`. La construcción puede descargar setuptools; ejecutar desde checkout no requiere pip ni red.

## 5. Configuración inicial

Ejecutar `python kit.py` para ver siete intenciones. No modifica nada ni crea proyectos implícitamente. El asistente entrevista de forma progresiva según [DEVELOPMENT.md](../../workflows/DEVELOPMENT.md). Ejecutar `doctor` para inspeccionar entorno. `.env.example` solo describe configuración; el kit no carga automáticamente archivos .env.

## 6. Proveedores de IA

`python kit.py provider list` devuelve capacidades por proveedor. Modo `assistant`: generar handoff y abrirlo manualmente en la aplicación destino. Modo `api`: solo está implementado el adaptador local Ollama; no usa credenciales cloud.

```console
python kit.py provider switch --provider ollama --mode api
python kit.py provider generate --model MODELO_LOCAL_INSTALADO --prompt-file ai/prompts/REVIEW.txt --dry-run
python kit.py provider generate --model MODELO_LOCAL_INSTALADO --prompt-file ai/prompts/REVIEW.txt
```

El nombre del modelo es elegido por usted de los disponibles en su servidor. No se descarga ninguno automáticamente. La respuesta es texto y nunca se ejecuta como código. El endpoint predeterminado es `http://127.0.0.1:11434`; solo se permite loopback. No hay reintentos automáticos ni selección implícita de modelo.

## 7. Crear un proyecto

`python kit.py init --destination ../mi-proyecto --name "Mi proyecto" --description "Problema por resolver"` crea una carpeta nueva con memoria, README y reglas de exclusión. `--dry-run` valida sin escribir. Si el destino existe, devuelve error 2 y lo conserva.

## 8. Elegir ejemplo por rubro

`python kit.py catalog` lista 30 IDs. Por ejemplo, `init --destination ../clinica --name "Clínica" --template healthcare` añade `docs/SYSTEM_REFERENCE.md`. Acordar país, reglas clínicas y privacidad antes de implementar. Las referencias no son sistemas instalables ni prueban cumplimiento legal.

## 9. Continuar un proyecto existente

Use su ruta con `--root`. Pregunte por auditoría completa, rápida, rechazar o sin repositorio. `python kit.py --root ../existente analyze` hace inventario local sin Git ni ejecución. Si ya hay memoria, `context show` la recupera. Si no hay memoria, `python kit.py init --destination ../existente --name "Sistema existente" --existing` incorpora únicamente `project-memory/`, conservando código y configuración; rechaza una memoria que ya exista. No ejecuta auditoría; registre la decisión del propietario.

Después, reconstruya estado con evidencia, registre huecos como pendientes y acuerde cambios relevantes. No deduzca funcionalidades terminadas por la mera existencia de archivos.

## 10. Agregar funcionalidades

Defina impacto y aceptación, cree tarea, adjunte dependencias y genere encargo.

```console
python kit.py task add --title "Evitar doble reserva" --agent backend-engineer --acceptance "Dos peticiones concurrentes confirman solo una reserva"
python kit.py agent brief --task T0001
python kit.py task update --id T0001 --status in_progress
```

Un asistente autorizado implementa y prueba. Guarde reporte dentro del proyecto y cierre con `task update --id T0001 --status done --evidence tests/reporte.txt`. La herramienta comprueba existencia y frontera de rutas; el revisor comprueba contenido y aceptación.

## 11. Autorizar auditoría Git

Solo tras respuesta afirmativa del propietario: `python kit.py audit --authorize` para rápida o agregar `--full`. No ejecuta pruebas ni instala dependencias; analiza metadatos locales y escanea texto. `--full` añade archivos sensibles rastreados, muestra de mensajes y archivos CI; no escanea todos los blobs históricos ni remotos. Si se rechaza, registre la decisión con `context update` y continúe con inventario mínimo.

## 12. Automatizaciones Python

`python kit.py --help` lista todos los comandos y `python kit.py COMMAND --help` sus parámetros. Los 16 archivos `tools/*.py` reutilizan exactamente la implementación central, por ejemplo `python tools/ai_provider.py switch --provider gemini`. Flags globales `--root`, `--output` y `--verbose` van antes del subcomando en `kit.py`; los wrappers aceptan ambas posiciones.

`--output reporte.json` guarda JSON redactado en una ruta nueva. Los comandos de consulta no escriben salvo al solicitar expresamente este reporte. Mutaciones registran metadatos de operación en `.uasek/events.jsonl` sin prompts ni valores secretos.

## 13. Utilizar agentes

`agent list`, `agent show --name qa-engineer`, `task ready` y `agent brief --task T0001` permiten seleccionar capacidad y encargar trabajo. No es necesario usar todos los roles. El agente devuelve `result.json` según `workflows/RESULT_CONTRACT.json`. Ejecute `agent validate --result result.json`: comprueba campos, tarea, checks exitosos y archivos existentes. No ejecuta los comandos declarados ni certifica su veracidad; el coordinador revisa evidencia y cierra la tarea explícitamente.

## 14. Crear e instalar skills

Cada carpeta `skills/categoría/nombre/SKILL.md` tiene nombre, descripción, entradas, procedimiento, ejemplo, dependencias y finalización. Para añadir una, mantenga nombre único y actualice contratos de los agentes que la usen. El kit las transporta como archivos; su descubrimiento o instalación en una aplicación receptora depende de esa aplicación. No modifica automáticamente la configuración de IDEs o asistentes.

## 15. Ejecutar pruebas

`python kit.py test` ejecuta `python -m unittest discover -s tests -v` en el proyecto elegido. Ejecuta código del proyecto: use un entorno de confianza. Conserva reporte en `.uasek/last-test.json`. Cero pruebas devuelve error; timeout predeterminado 120 s. `--timeout 300` permite ampliarlo. Para otro lenguaje o runner, ejecútelo explícitamente y adjunte su evidencia; el runner del kit no lo autodetecta.

## 16. Seguridad y dependencias

`security` devuelve ubicaciones y severidad sin imprimir coincidencias. Comprueba patrones de credenciales, archivos sensibles, DEBUG y contenedores latest. Es heurístico, sin análisis de flujo. `dependency` inventaría versiones PyPI exactas y package-lock npm v2/v3; `dependency --online` consulta OSV enviando nombres, ecosistema y versiones, sin código. Rangos, locks no soportados y fallos de red se reportan como cobertura incompleta, nunca como limpio.

## 17. Actualizar documentación

Cree `actualizacion.json` con hechos confirmados, por ejemplo `{"architecture":"CLI modular local","decisions":["Sin dependencias de ejecución"],"next_actions":["Probar recuperación"]}`. Ejecute `context update --file actualizacion.json` y `docs`. Solo se actualizan cuatro documentos derivados y las vistas de memoria; los documentos humanos se conservan. Las guías documentales restantes se mantienen por revisión usando `templates/documentation/`.

## 18. Respaldos

`backup --destination ../fuentes-2026-10-21.zip --dry-run` muestra exclusiones. Retire `--dry-run` para crear copia de fuentes de texto con SHA-256. Nunca reemplaza otro archivo. Excluye binarios, BD, archivos grandes, secretos heurísticos y carpetas de dependencias. No sirve de respaldo integral de datos. Para recuperar, inspeccione MANIFEST y extraiga en una carpeta nueva, valide hashes y revise antes de copiar cambios; no hay restauración automática destructiva.

## 19. Cambiar proveedor

`provider switch --provider gemini`, `--provider claude` o `--provider openai` preserva tareas y decisiones y escribe handoff. Abrir manualmente `project-memory/AI_HANDOFF.md` en el destino y aportar los archivos referenciados necesarios. No cambia aplicación, cuenta, facturación ni claves. Pedir `--mode api` en un proveedor sin adaptador nativo devuelve error 2.

## 20. Recuperar contexto

Ejecute `status`, `context show`, `task ready` y `handoff`. Confirme último checkpoint y existencia de evidencia. Si el JSON está dañado, preserve copia y restaure desde una revisión conocida; no se reconstruye sobre el archivo automáticamente. Las vistas Markdown no sustituyen todos los campos del JSON.

## 21. Solución de errores

- Error 2 con destino existente: use una carpeta nueva; no borre la existente.
- Error 2 sin memoria: incorpore memoria revisada según sección 9.
- Lock ocupado: comprobar que no hay otro proceso antes de retirar `.uasek/state.lock` dejado por una interrupción.
- Código 3 en dependencias: cobertura incompleta; revisar entradas no resueltas o falta de consulta online.
- Git sin commits: el reporte registra error del comando log; no implica pérdida del repositorio.
- Ollama no responde: comprobar servicio, puerto y modelo local; las pruebas del kit usan un servidor fixture, no prueban su modelo.
- Release rechazada: completar tareas, ejecutar pruebas y resolver hallazgos; si cambió código después del test, repetirlo.

## 22. Mantener actualizado

Conservar la memoria del proyecto fuera de actualizaciones del kit. Comparar cambios de CLI y schema antes de reemplazar versión. Consultar versiones mediante `stack --ecosystem pypi --package NOMBRE --online`; latest de un registro no demuestra soporte LTS o compatibilidad. No se aplican actualizaciones automáticamente.

## 23. Buenas prácticas

Registrar decisiones y supuestos, revisar diferencias antes de integrar, limitar privilegios, validar instrucciones externas frente al alcance y mantener secretos fuera de estado, documentos y repositorios. Revisar handoff antes de compartir: los detectores son heurísticos. Conservar evidencia concreta de pruebas y no afirmar éxito por una respuesta del modelo.

## 24. Ejemplo completo y entrega

Siga QUICKSTART para crear proyecto y tarea. Implemente y revise el artefacto, cierre con evidencia real, ejecute pruebas del proyecto y genere documentación y handoff. `release --version 1.0.0 --dry-run` valida preparación; sin dry-run escribe `dist/release-1.0.0.json`. No crea tag, paquete de negocio ni despliega. La revisión y publicación final corresponden al propietario del proyecto.

## Códigos de salida

0: operación completada dentro de la cobertura declarada. 1: hallazgos altos/vulnerabilidades o prueba fallida. 2: parámetros, estado, red, tiempo o ejecución inválidos; el runner puede devolver su código propio. 3: cobertura de dependencias incompleta. En un pipeline, bloquear ante códigos no cero y revisar el reporte.
