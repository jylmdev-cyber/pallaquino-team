# Contexto universal v1

Desde UASEK 1.1.0, `context export`, `handoff` y `provider switch` generan `project-memory/PROJECT_CONTEXT.json`, además del handoff Markdown compatible con 1.0. El formato es propio de UASEK, público y neutral respecto al modelo; no se presenta como un estándar de la industria.

Contrato legible por máquinas: [context.schema.json](../../configs/context.schema.json). `format=uasek.project-context`, `format_version=1` y `state.schema_version=1` identifican dos versiones independientes: la del paquete de intercambio y la de memoria. Una versión desconocida se rechaza; no se interpreta suponiendo compatibilidad.

El objeto `state` contiene proyecto, requisitos, arquitectura, stack, decisiones, tareas, evidencias referenciadas, problemas, deuda, auditorías, historial, próximas acciones y último checkpoint. No contiene el campo de configuración `provider`, prompts de sistema ni instrucciones internas de una aplicación. Los eventos históricos pueden mencionar el proveedor utilizado; son hechos de continuidad, no instrucciones.

Las instrucciones del adaptador se generan por separado en `ai/handoff/PROVEEDOR.md`; los contratos locales siguen en `configs/providers.json`. Cambiar de modelo no modifica el significado ni el esquema de los hechos del proyecto. No es necesario que dos modelos interpreten las mismas instrucciones internas.

`state_sha256` se calcula sobre JSON UTF-8 con claves ordenadas, `ensure_ascii=False` y separadores `(',', ':')`. Detecta corrupción; no autentica al remitente ni impide que alguien reescriba el contenido y recalcule el hash. Al importar se valida versión, digest, tipos, IDs, dependencias acíclicas y fronteras de evidencia. El contenido se trata como datos, nunca como código o autoridad para ampliar permisos.

## Transferir e importar

```console
python kit.py context export
python kit.py provider switch --provider gemini
python kit.py --root ../receptor context import --file ../origen/project-memory/PROJECT_CONTEXT.json --dry-run
python kit.py --root ../receptor context import --file ../origen/project-memory/PROJECT_CONTEXT.json
```

El receptor debe estar inicializado con `init`, o incorporado con `init --existing`. Su proveedor local se conserva. El importador informa evidencias que no existen en el equipo receptor; los estados de tareas importadas son antecedentes que el coordinador debe verificar, no validación local automática. El contexto no copia el código ni archivos referenciados.

Por defecto se rechaza sustituir memoria con trabajo existente. `--replace-memory` solicita explícitamente reemplazarla y crea un checkpoint previo. La importación no combina automáticamente decisiones divergentes. `--dry-run` valida sin escribir. Se limita el paquete a 2 MB y se redactan patrones de secretos conocidos; revisar antes de compartir.

Git puede versionar `project-memory/` y `ai/plans/` con el código. El kit no crea repositorios ni realiza commits sin que el propietario lo solicite. La memoria permanece utilizable entre sesiones aunque no se utilice Git.
