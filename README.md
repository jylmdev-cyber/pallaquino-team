# PALLAQUINO TEAM — 2.0.0

Infraestructura operativa en español para coordinar ingeniería asistida por IA: tareas con dependencias, contratos de agentes, memoria portable, herramientas de inspección, pruebas, respaldo y continuidad. Núcleo Python sin dependencias externas de ejecución.

**PALLAQUINO TEAM** es el nombre del proyecto. El núcleo conserva los identificadores técnicos `uasek` y `universal-ai-software-kit` para mantener la compatibilidad de comandos, instalación y formatos de memoria.

**UNIVERSAL DOCUMENTATION PORTAL (UDP)** incorpora guías navegables, búsqueda local, catálogos generados, diagramas y tema claro/oscuro. [Administración del portal](documentation/PORTAL_MANUAL.md). Está preparado para GitHub Pages con publicación deshabilitada hasta autorización.

```console
python tools/docs_manager.py generate
cd documentation/portal
npm ci --ignore-scripts
npm run dev
```

**ENGINEERING INTELLIGENCE PLATFORM** añade PROJECT BRAIN, trabajos paralelos con reservas de archivos, cuatro niveles de autonomía, quality gates obligatorios, recuperación, selección de modelos, extensiones revisadas, gestión multiproyecto y centro de operaciones HTML opcional. [Manual de plataforma y límites](docs/platform/PLATFORM.md).

```console
python kit.py platform init
python kit.py platform plan --request "Agregar API de autenticación"
python kit.py platform map
python kit.py platform search --query "arquitectura"
python examples/platform/demo.py --destination ../demo-eip --approve-demo
```

La plataforma es optativa por proyecto. Una vez inicializada, los comandos de escritura/ejecución respetan su política; consulte `--policy-preview` y aprobaciones. La demostración usa dos scripts locales conocidos, permisos explícitos y gates; no despliega sistemas ni requiere un modelo.

Desde 1.1: [contexto universal importable](docs/continuity/CONTEXT_FORMAT.md), [checkpoints recuperables](docs/continuity/CHECKPOINTS.md) y [selección automática y limitada de roles](docs/workflows/ADAPTIVE_ORCHESTRATION.md). Las instrucciones de proveedores se mantienen separadas de los hechos del proyecto.

```console
python kit.py
python kit.py doctor
python kit.py catalog
python kit.py init --destination ../mi-proyecto --name "Mi proyecto" --template inventory
python kit.py --root ../mi-proyecto task add --title "Definir alcance" --agent product-owner --acceptance "Reglas y actores acordados"
python kit.py --root ../mi-proyecto agent brief --task T0001
python kit.py --root ../mi-proyecto handoff
python kit.py test
```

`python kit.py` muestra el menú de intención sin modificar archivos. La entrevista progresiva se realiza con el asistente siguiendo [el protocolo](workflows/DEVELOPMENT.md); los comandos explícitos ejecutan las operaciones locales.

## Contenido

- 21 perfiles con contratos completos en [configs/agents.json](configs/agents.json).
- 31 skills operativas en `skills/`, 16 entradas de compatibilidad `tools/*.py`, el administrador UDP `tools/docs_manager.py` y un CLI central.
- 30 referencias por industria consultables con `catalog` y seleccionables con `init --template`.
- PROJECT MEMORY JSON y vistas Markdown; exportación de diez secciones y cambio de proveedor.
- Auditoría Git autorizada, escaneo heurístico, consulta OSV opcional y comprobación de registros PyPI/npm.
- Pruebas unittest, pipeline de validación, documentación técnica y manual de usuario.

## Capacidades y límites

Los agentes son contratos y encargos persistentes para asistentes o personas. El coordinador usa `task ready`, `agent brief`, `agent validate` y revisión de evidencia; no hay un enjambre autónomo de 21 modelos ni ejecución automática de sus respuestas.

Ollama tiene cliente HTTP local de inferencia de texto. OpenAI/ChatGPT, Claude, Gemini, Copilot, Cursor, Windsurf, OpenRouter y otros se soportan mediante transferencia manual de contexto; no se incluyen clientes de API cloud ni se cambia la aplicación del usuario.

Las 30 referencias son especificaciones adaptables, no aplicaciones comerciales implementadas. Los controles de seguridad son parciales y reportan cobertura. El respaldo incluido es de fuentes de texto, no de producción. El runner incluido usa unittest; otros lenguajes usan su runner externo y adjuntan evidencia. No hay despliegue ni publicación automática.

## Empezar y continuar

Leer [QUICKSTART](QUICKSTART.md), [manual de usuario](docs/user-manual/MANUAL.md), [manual técnico](docs/technical-manual/MANUAL.md) y [reporte de validación](docs/quality/VALIDATION_REPORT.md). La instalación recomendada es extraer el ZIP y ejecutar desde el checkout. Instalación de CLI con pip es opcional.

La auditoría autorizada del remoto inicial confirmó que estaba vacío. Las pruebas Git crean repositorios temporales propios. Ninguna herramienta realiza reset, force push, eliminación de ramas o despliegues. Datos del repositorio y publicación: [REPOSITORY](docs/operations/REPOSITORY.md).
