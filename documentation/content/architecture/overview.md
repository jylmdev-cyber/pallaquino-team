# Arquitectura de la plataforma

El núcleo es independiente del proveedor de IA. La CLI recibe una raíz de proyecto; las operaciones separan recursos del kit, memoria del proyecto y artefactos temporales. El portal es una capa estática derivada: no cambia el motor de ejecución ni recibe credenciales.

## Contexto C4

Representación de los límites implementados; los proveedores cloud se usan por transferencia manual, salvo que se incorpore un adaptador revisado.

```mermaid
flowchart LR
  User[Persona o asistente autorizado] --> CLI[CLI Python]
  CLI --> Kit[PALLAQUINO TEAM]
  Kit --> Memory[Archivos de proyecto]
  Kit --> Local[Procesos locales revisados]
  Kit --> Ollama[Ollama local opcional]
  Kit -. Contexto universal manual .-> Cloud[Otros proveedores IA]
  Docs[Portal estático UDP] --> Reader[Consulta en navegador]
```

## Contenedores y componentes C4

```mermaid
flowchart TB
  CLI[kit.py y tools] --> Core[Memoria y operaciones UASEK]
  CLI --> EIP[Engineering Intelligence Platform]
  EIP --> Brain[Brain y trazabilidad]
  EIP --> Policy[Permisos y gates]
  EIP --> Engine[Scheduler y workers]
  Engine --> Workspace[Workspace exclusivo por trabajo]
  Core --> Files[(JSON y Markdown versionados)]
  Brain --> Files
  Engine --> Review[Revisión e integración]
  Review --> Checkpoint[Checkpoint y journal]
  Sources[Fuentes públicas permitidas] --> UDP[docs_manager]
  UDP --> Build[VitePress estático]
```

## Estructura de carpetas

| Carpeta | Responsabilidad |
|---|---|
| `uasek/` | Núcleo operativo y generador UDP |
| `uasek/eip/` | Estado, gobierno, ejecución, brain y adaptadores |
| `configs/` | Catálogos y esquemas versionados |
| `agents/`, `skills/` | Contratos e instrucciones |
| `tools/`, `scripts/` | Entradas CLI y empaquetado |
| `project-memory/` | Estado local y checkpoints; excluido del portal público |
| `.uasek/` | Workspaces y aprobaciones privadas; no versionado |
| `docs/` | Documentación fuente existente |
| `documentation/content/` | Guías manuales del portal |
| `documentation/portal/` | Framework, tema y contenido generado |

## Modelo de datos simplificado

```mermaid
erDiagram
  PROJECT ||--o{ TASK : contiene
  PROJECT ||--o{ RECORD : conserva
  TASK ||--o{ JOB : vincula
  RUN ||--o{ ATTEMPT : ejecuta
  JOB ||--o{ ATTEMPT : registra
  JOB ||--o{ ARTIFACT : entrega
  RECORD ||--o{ EVIDENCE : referencia
  TRACE ||--o{ RELATION : vincula
```

Es un mapa lógico, no un esquema SQL. Las dependencias y relaciones se almacenan en JSON. La [referencia EIP](/generated/reference/docs/platform/PLATFORM.html) detalla nombres reales y restricciones.

## Decisiones y dependencias

Python estándar permite ejecutar el núcleo sin framework web ni base de datos. VitePress agrega dependencias solo al build documental, con versiones directas y lockfile fijados. Las instrucciones de proveedores se separan del contexto universal; importar hechos no importa permisos. La [decisión del motor](/generated/reference/documentation/ENGINE_DECISION.html) documenta las alternativas evaluadas.

[Manual técnico](/generated/reference/docs/technical-manual/MANUAL.html) · [Firmas extraídas del código](/generated/api/index.html)
