---
layout: home
title: Documentación de PALLAQUINO TEAM
hero:
  name: PALLAQUINO TEAM · DOCUMENTACIÓN
  text: Ingeniería con contexto. Entregas con evidencia.
  tagline: La guía de tu equipo de software asistido por IA. Memoria portable, roles modulares y automatización bajo tu control.
  image:
    src: /logo.svg
    alt: Identidad de PALLAQUINO TEAM
  actions:
    - theme: brand
      text: Comenzar →
      link: /getting-started/install
    - theme: alt
      text: Ver arquitectura
      link: /architecture/overview
    - theme: alt
      text: Repositorio GitHub ↗
      link: https://github.com/jylmdev-cyber/pallaquino-team
features:
  - title: Un contexto que continúa
    details: Conserva decisiones, requisitos y evidencias en formatos abiertos. Retoma el proyecto con otro asistente sin reconstruir su historia.
    link: /integrations/providers
    linkText: Transferir contexto
  - title: Roles para cada tarea
    details: Selecciona los perfiles necesarios. Coordina dependencias y archivos compartidos con presupuestos y límites explícitos.
    link: /generated/agents/index
    linkText: Explorar agentes
  - title: Calidad antes de integrar
    details: Aplica pruebas, permisos, revisión y checkpoints. Una tarea no termina hasta satisfacer sus controles obligatorios.
    link: /security/overview
    linkText: Conocer los controles
---

<PortalStatus />

## Tu primera consulta

Desde la raíz del checkout, comprueba el entorno y consulta la ayuda:

```console
python kit.py doctor
python kit.py --help
python kit.py status
```

La demostración EIP ejecuta dos scripts locales conocidos con aprobaciones y genera un centro de operaciones HTML. Usa una carpeta nueva:

```console
python examples/platform/demo.py --destination ../demo-eip --approve-demo
```

## Explorar documentación

| Quiero… | Ir a |
|---|---|
| Entender el alcance y los conceptos | [Introducción](introduction/overview.html) |
| Instalar en mi equipo | [Instalación](getting-started/install.html) |
| Comprender los componentes | [Arquitectura](architecture/overview.html) |
| Implementar un cambio | [Desarrollo](development/workflow.html) |
| Elegir un responsable | [Agentes](generated/agents/index.html) |
| Aplicar una capacidad | [Skills](generated/skills/index.html) |
| Ejecutar automatizaciones | [Scripts](generated/scripts/index.html) |
| Revisar permisos y seguridad | [Seguridad](security/overview.html) |
| Cambiar de proveedor | [Integraciones](integrations/providers.html) |
| Consultar contratos y comandos | [API y CLI](api/overview.html) |
| Adaptar una referencia sectorial | [Ejemplos por rubro](generated/examples/index.html) |
| Resolver un error | [Solución de problemas](troubleshooting/common.html) |

[Estado y versiones](changelog/versions.html) · [Contribuir](development/contributing.html) · [Licencia MIT](generated/reference/LICENSE.html) · [Administrar este portal](generated/reference/documentation/PORTAL_MANUAL.html)
