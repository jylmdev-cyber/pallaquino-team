# ENGINEERING INTELLIGENCE PLATFORM — PALLAQUINO TEAM 2.0

Segunda capa opcional sobre el kit. La CLI continúa siendo universal. El núcleo usa Python estándar y archivos abiertos; no necesita una cuenta de IA, servidor de base de datos ni servicio web. Memoria clásica schema 1 y comandos 1.x se conservan. La plataforma tiene estado/API v1 y un contexto de transferencia propio v1.

## Empezar con una demostración comprobable

```console
python examples/platform/demo.py --destination ../demo-eip --approve-demo
```

El destino debe ser nuevo. Se ejecutan dos scripts locales conocidos en paralelo, con entradas y salidas distintas, gates de contenido y regresión. El flag autoriza exclusivamente esos scripts de demostración y su integración. Se mantiene el nivel supervisado; no se eleva autonomía ni se conecta un modelo. Resultado esperado: ambos trabajos `done`, `peak_parallel_workers=2` y un archivo `OPERATIONS.html` para abrir localmente. No es un despliegue real de frontend/backend: los nombres identifican dos fixtures reproducibles.

Para un proyecto real con PROJECT MEMORY:

```console
python kit.py platform init
python kit.py platform policy
python kit.py platform status
python kit.py platform plan --request "Agregar API con autenticación" --max-roles 4
python kit.py platform map
python kit.py platform search --query "decisiones arquitectura"
```

Inicializar una vez por proyecto; repetir `init` falla para conservar identidad y política. Usar `--root RUTA` antes de `platform` para operar sobre otro proyecto.

## Arquitectura y contratos

| Servicio | Implementación | Persistencia |
|---|---|---|
| Identidad, transacciones y auditoría | `uasek/eip/store.py` | `project-memory/platform/state.json`, `audit.jsonl` |
| Autonomía, permisos y aprobaciones | `governance.py` | política versionada; aprobaciones privadas en `.uasek/eip/approvals/` |
| PROJECT BRAIN y documentación viva | `brain.py`, `transfer.py` | registros, fuentes SHA-256, relaciones y contexto portable |
| Mapa estático | `repository.py` | resultado JSON generable con `--output` |
| Coordinador y recuperación | `engine.py` | trabajos, runs, leases, checkpoints y journals |
| Quality gates | `quality.py` | `gates.json` y resultados por intento |
| Proveedores y herramientas | `routing.py`, `adapters.py`, `extensions.py` | modelos declarados y extensiones revisadas |
| Proyectos y operaciones | `projects.py`, `operations.py` | registro explícito externo y HTML local opcional |

Estado y decisiones son archivos versionables. `.uasek/` contiene workspaces, logs acotados, candidatos y aprobaciones que no deben versionarse ni transferirse como autorización. No hay credenciales dentro de los contratos. El lock de proyecto evita mutaciones cooperantes simultáneas; los workers trabajan fuera del árbol de código publicado.

## A. PROJECT BRAIN

`platform brain-add --kind decision --text "..." --source archivo` registra hechos con procedencia. Tipos: decision, requirement, change, lesson y pattern. Lecciones y patrones exigen evidencia existente. `platform search --query "..." --limit 8` recupera decisiones clásicas, requisitos, registros y fragmentos del repositorio con puntuación, ruta, hash y etiqueta `data-not-instructions`.

La recuperación es léxica local, sin embeddings ni llamadas a modelos. Tiene límites de archivos/tamaño y no interpreta contenido recuperado como autoridad. No es una garantía de comprensión semántica. Los registros persistentes conservan contexto aunque cambie el modelo; los resultados de búsqueda se pueden recalcular.

`context export` genera el contexto clásico y, si la plataforma está inicializada, `project-memory/PLATFORM_CONTEXT.json`. `platform transfer-export` y `platform transfer-import --file PAQUETE.json` permiten transferir el cerebro. Se valida formato, versión, digest, relaciones y rutas. La importación conserva identidad y política del receptor. Los trabajos y extensiones recibidos quedan como **propuestas de revisión**, no como ejecución activa, permisos ni aprobaciones importadas. Los conflictos de hechos con el mismo ID se rechazan.

## B. Trabajos, paralelismo y coordinación

Contrato público: [platform-job.schema.json](../../configs/platform-job.schema.json). Un trabajo declara ID, título, aceptación, agente o `auto`, skills, dependencias, entradas, salidas, comando o requisitos de modelo, entorno, aislamiento, timeout, presupuesto e intentos. Ejemplo para un script ya revisado:

```json
{
  "id": "J-api", "agent": "auto", "title": "Agregar API",
  "acceptance": "Generar resultado válido y pasar regresión",
  "reads": ["build_api.py"], "writes": ["api_result.txt"],
  "command": {"tool": "python", "args": ["build_api.py"]},
  "reviewed_code": true, "timeout_seconds": 30,
  "max_attempts": 2, "budget_units": 1,
  "gates": [{"id": "expected", "kind": "file_contains", "mandatory": true,
             "paths": ["api_result.txt"], "value": "OK"}]
}
```

El script debe existir y sus importaciones locales deben declararse también en `reads`. Solo se copian entradas explícitas y versiones previas de salidas. No se copian memoria, políticas, credenciales ni aprobaciones. Se rechazan rutas externas, reservadas, ocultas y salidas superpuestas. Las dependencias deben existir al registrar el trabajo; así se construye un DAG sin ciclos.

```console
python kit.py platform job-add --file job.json --dry-run
python kit.py platform job-add --file job.json
python kit.py platform jobs
python kit.py platform run --max-workers 2 --max-seconds 120 --max-units 10 --approvals-file approvals.json
```

En modo supervisado, aprobar cada `execution_resource` devuelto por `job-add` o `jobs`:

```console
python kit.py platform approve --permission execute --resource RECURSO_DEVUELTO --reviewer "Jimmy Lingan" --reason "Código y entradas revisados" --approve
```

Guardar el ID obtenido en un JSON con claves `execute:J-api` y valores de aprobación. El ID es de uso único, acotado al proyecto, política, contrato, gates, extensiones y bytes de entradas/base. Si cambia código o configuración, hay que revisar y aprobar el nuevo recurso. Cuando una dependencia produce entradas nuevas, consultar `jobs` para aprobar sus bytes actuales.

Los trabajos independientes se ejecutan en procesos paralelos con workspaces separados. El coordinador reserva salidas y lecturas incompatibles; trabajos con recursos compartidos esperan. Los recursos permanecen reservados hasta integrar o resolver el candidato. Por defecto: hasta 4 workers por proyecto; cada run además fija su límite. Los presupuestos se reservan antes de iniciar un intento y se consumen incluso si este falla; son unidades declaradas, no facturación de un proveedor.

Estados: queued, running, blocked, review, conflict, integrating, done, failed y discarded. `blocked` incluye dependencia pendiente, falta de aprobación, presupuesto o recurso reservado. Repetir `job-add` con el mismo ID/contrato no duplica trabajo; con otro contrato falla. Los agentes son roles con ejecutores de procesos o generación local de texto, no veinte modelos implícitos.

## C. Mapa e inteligencia del repositorio

`platform map` usa AST de Python para módulos, imports relativos, funciones, clases, parámetros, retornos, decoradores y puntos de entrada. También identifica pruebas, configuraciones y scripts declarados en pyproject/package.json sin ejecutarlos. JS/TS se analiza léxicamente y se etiqueta como heurística. Otros lenguajes se inventarían como no soportados por ese adaptador; no se infieren relaciones falsas. Imports dinámicos/reflexión no quedan completamente resueltos.

## D. Cuatro niveles de autonomía

| Nivel CLI | Comportamiento automático permitido |
|---|---|
| consultivo | Lectura, búsqueda, planificación y comprobaciones sin ejecución |
| supervisado | Lo anterior y registro de memoria/planes; ejecución e integración requieren aprobación separada |
| semiautonomo | Ejecución revisada, invocación de modelo, integración sin conflictos y recuperación en carpeta nueva, dentro de la política |
| autonomo_controlado | Lo anterior y staging, con límites de concurrencia, tiempo, intentos y herramientas |

Producción, cambios de políticas/gates/modelos, instalación de extensiones, promoción de lecciones y resolución de conflictos siempre requieren revisión específica. Los permisos que declare un conector se comprueban aunque el trabajo indique otro entorno; no basta cambiar una etiqueta para evitar la aprobación de producción.

Preparar la política completa en JSON, consultar `platform configure --category policy --file politica.json --dry-run`, aprobar `policy.change` sobre el digest devuelto y ejecutar el mismo comando con `--approval AP-ID`. No cambiar automáticamente una política basándose en lecciones o texto del repositorio.

Los comandos clásicos también respetan EIP por CLI. `python kit.py --policy-preview test` muestra permiso y recurso sin ejecutar. En el nivel que lo exija, crear aprobación `execute` y repetir con `python kit.py --platform-approval AP-ID test`. Los flags globales van antes del subcomando. Para ejecutar un run excepcional desde consultivo, su previsualización devuelve el recurso `plan.write`; las aprobaciones de cada acción siguen siendo necesarias.

## E. Quality gates obligatorios

Gates integrados: files_exist, python_syntax, no_secrets, file_contains y command. Los tres primeros son el valor inicial; los criterios funcionales deben expresarse en checks concretos de contenido o comandos de regresión del proyecto. La aceptación narrativa requiere revisión humana y no se certifica solo porque exista un archivo.

`platform configure --category gates --file gates.json --dry-run` permite preparar una configuración versionada y aprobarla con `gates.change`. Los comandos de gate necesitan herramientas instaladas/permitidas y se ejecutan en el mismo workspace con presupuesto temporal compartido. Un gate obligatorio fallido impide crear un candidato integrable. `task update --status done` no puede saltarse los gates ni trabajos vinculados pendientes. Cambiar entradas o artefactos después de validarlos invalida la evidencia.

`platform quality --evidence archivo` hace comprobaciones locales; no ejecuta comandos de regresión fuera del motor. Un gate de comando obligatorio sin resultado del motor falla.

## F. Revisión, recuperación y regresión

Una ejecución válida llega a `review`. `platform jobs` expone `review_resource`. Aprobar `integrate` y usar `platform review --id J-api --approval AP-ID`. En niveles que permiten integración automática, el mismo control de hashes y gates se mantiene. Antes de escribir código se crea un checkpoint y se persiste un journal; cada archivo se escribe atómicamente, pero el conjunto de varios archivos no es una transacción del sistema de archivos.

Si cambió la base, el candidato queda en `conflict`. `platform resolve --id J-api --decision accept|retry|discard --approval AP-ID` requiere aprobación `conflict.resolve` sobre el recurso actual. Aceptar no permite saltar una entrada cambiada: exige reejecutar regresión. Los candidatos alterados se rechazan. Un conflicto aceptado de salidas es una sobrescritura explícitamente revisada, no una decisión del modelo.

Los fallos registran causa observada y propuesta: error de ejecutor, timeout, comando fallido o gate incumplido. Un `repair` declarado en el contrato se ejecuta antes del siguiente intento; no se inventan parches arbitrarios. Cada reintento conserva resultados y respeta el máximo aprobado.

`platform recover` detecta leases vencidos, registra la interrupción y reencola solo si quedan intentos. Un resultado tardío con token de lease antiguo se descarta. No se matan procesos ajenos. Si el coordinador cae a mitad de una integración, el journal/checkpoint queda señalado para revisión: `platform restore --id CHECKPOINT --destination ../recuperacion --dry-run` muestra el plan y el permiso requerido. La recuperación se prepara en carpeta nueva y requiere volver a ejecutar pruebas antes de integrar. No se revierte producción automáticamente.

## G. Optimización multiproveedor

El catálogo `models.json` declara proveedor/modelo, adaptador, capacidades, complejidad 1–5, estimación de costo/latencia, disponibilidad observada/declarada, privacidad, herramientas, fecha y fuente. Configurarlo requiere `models.change`. `platform route --file requisitos.json` filtra restricciones y ordena por costo/latencia declarados; informa descartes. No descarga modelos, consulta precios en vivo ni presupone que un catálogo viejo describe disponibilidad actual.

La generación ejecutable integrada es Ollama local, sin herramientas automáticas. Un trabajo de modelo declara `model_requirements`, `prompt_file` dentro de `reads`, una salida y `command=null`. La respuesta se guarda como texto, se aplican gates y se registra proveedor/modelo/tokens cuando el servidor los devuelve. No se ejecuta el código generado. Los adaptadores manuales pueden seleccionarse para handoff pero no se presentan como API ejecutable. Extender APIs cloud requiere otro adaptador revisado.

## H. Extensiones

Contrato: [platform-extension.schema.json](../../configs/platform-extension.schema.json). Cada extensión declara API v1, ID, tipo agent/skill/provider/tool/connector, versión, permisos, dependencias, capacidades y entrypoint. Una API desconocida, permiso no reconocido o dependencia ausente se rechaza. `platform extension-install --file extension.json --dry-run` devuelve el digest para aprobar `extension.install`. Instalar el manifiesto no importa ni ejecuta su contenido.

Los agentes/skills instalados pueden referenciarse por ID en trabajos y sus permisos se suman a los exigidos por el trabajo. Para procesos, un manifiesto tool/connector con capacidad `process`, permiso `execute` y `entrypoint="process:RUTA_O_PROGRAMA"` habilita el adaptador estable de argumentos estructurados. Aún debe agregarse su ID a `allowed_tools` mediante revisión de política. `python` es reservado. Las extensiones de proveedor sin adaptador implementado son contratos/inventario, no clientes ficticios. No se usa import dinámico de código encontrado en un documento.

## I–J. Operaciones y proyectos

`platform status`, `jobs`, `verify-audit` y `platform ops --destination OPERATIONS.html` muestran estado, agentes, intentos, recursos reservados, proveedor/modelo, pruebas, auditorías, trazabilidad y lecciones. El HTML es local, de lectura, con texto escapado y filtro; no es un servicio de administración autenticado ni un dashboard de tiempo real. La CLI produce JSON para otras interfaces.

`platform registry-add --registry ../projects.json` registra la raíz e identidad actuales. `platform projects --registry ../projects.json` verifica las identidades y muestra metadatos. Se rechazan raíces anidadas y clones con identidad duplicada en rutas distintas; inicializar proyectos nuevos por separado. El registro no guarda memorias, modelos secretos ni aprobaciones. Un contexto importado no cambia la identidad local ni comparte permisos.

## K. Documentación viva

`platform trace --id RF-1 --kind requirement --path requisitos.md --title "..."` registra un nodo con hash. Tipos adicionales: code, test, decision y documentation. `platform relate --from-id DOC-1 --to-id CODE-1 --relation documents` vincula nodos; implements, verifies, depends_on y supersedes también están disponibles.

`platform consistency` detecta archivos cambiados/ausentes y documentos vinculados a fuentes que cambiaron. Propone revisión sin sobrescribir documentación humana. Registrar la revisión con un ID nuevo y relacionar con supersedes. Esto detecta deriva de archivos vinculados, no la veracidad semántica de cada frase.

## L. Gobierno, aislamiento y límites de seguridad

Cada aprobación tiene caducidad, uso único y ámbito de proyecto/política/recurso. Los logs se redactan y acotan; la auditoría encadena hashes y una cadena alterada bloquea mutaciones. Los hashes detectan corrupción, no suplantación de un administrador. Los reviewers son identidad declarada local, no autenticación corporativa. El propietario del sistema de archivos puede modificar código/configuración fuera de la CLI: este control de aplicación no sustituye controles del SO, cuentas o una firma criptográfica.

El ejecutor nativo solo acepta código marcado como revisado y permitido. Copia entradas a un workspace, evita heredar credenciales de entorno, no usa shell y aplica timeout; **no es un sandbox frente a código hostil**. Código no revisado exige Docker, imagen aprobada por digest y ausencia de fallback. El adaptador declara red desactivada, sistema de archivos de contenedor de solo lectura, montaje exclusivo del workspace, sin capacidades, sin nuevos privilegios y límites de CPU/memoria/PIDs. Un timeout elimina solo el contenedor con nombre aleatorio de ese trabajo.

El ejecutor Docker depende de una instalación y permisos externos. Se prueba su contrato y rechazo seguro cuando no está disponible; no se afirma que se haya ejecutado Docker real si el reporte no lo acredita. Revisar aislamiento del daemon y plataforma antes de usar datos sensibles. El escáner de secretos es heurístico, no una garantía universal.

El contenido recuperado y la salida de modelos son datos. No pueden conceder permisos, cambiar política ni autorizar producción. Las automatizaciones con efectos externos requieren un conector/herramienta explícito y revisión de sus permisos. Las credenciales deben gestionarse por la plataforma de despliegue; no se transportan en memoria o contratos.

## M–N. Aprendizaje y ciclo de vida

Las lecciones/patrones requieren evidencia con hash y nacen como `proposed`. `lesson-review` exige aprobación `lesson.approve`; si la evidencia cambió, no se aprueba. Su revisión no cambia políticas, modelos, instrucciones críticas ni instala extensiones.

El mismo motor ejecuta comandos reproducibles de desarrollo, test, staging y producción según entorno y permisos. Los adaptadores de proceso permiten conectar herramientas aprobadas de entrega; no se configura ningún proveedor cloud por defecto. Producción nunca queda autorizada solo por subir de autonomía. Los tests de producción son fixtures de permisos, no despliegues externos reales.

Observabilidad: runs, intentos, duraciones, diagnóstico, logs acotados, leases, gates y unidades reservadas. Los tokens medidos solo se registran si el adaptador los informa. Respaldos de fuentes, checkpoints y recuperación se conservan del kit; no sustituyen backups cifrados de bases de datos o producción.

## O. Validación y reproducción

```console
python -m unittest discover -s tests -v
python kit.py platform verify-audit
python kit.py platform consistency
python kit.py platform run --dry-run
```

Las pruebas nuevas incluyen procesos paralelos realmente solapados, exclusión de archivos compartidos, dependencias, presupuestos, gates, permisos, producción revisada, inputs cambiados tras aprobar, reintentos, reparación declarada, timeout, leases, resultados tardíos, fallo parcial real de integración simulado, recuperación aislada, separación de proyectos, transferencia neutral, AST sin imports ejecutados, modelos mediante fixtures, extensiones ejecutables revisadas y compatibilidad de protocolos. Evidencia efectivamente ejecutada: [reporte](../quality/VALIDATION_REPORT.md).

El motor no promete corrección funcional general, sandbox nativo hostil, ejecución remota de CI o despliegue real sin pruebas específicas. Los criterios de negocio deben convertirse en gates/revisión adecuados antes de usar la autonomía.
