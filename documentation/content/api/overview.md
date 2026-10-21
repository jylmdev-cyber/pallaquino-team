# Contratos, CLI y API interna

La interfaz universal del proyecto es una **CLI**. No existe un servidor REST implementado ni endpoints de producción que documentar con OpenAPI. Las plantillas API son referencias para futuros sistemas.

## Referencia generada

- [Todos los comandos y sus flags](/generated/cli/index.html).
- [Funciones y clases Python](/generated/api/index.html), extraídas con AST sin importar ni ejecutar módulos descubiertos.
- [Scripts de compatibilidad](/generated/scripts/index.html).

## Ejemplos reales

```console
python kit.py --help
python kit.py platform --help
python kit.py --root ../mi-proyecto status
python kit.py orchestrate --request "Documentar una API"
```

Los flags globales se colocan antes del subcomando; los wrappers admiten los flags heredados indicados por su ayuda. Una referencia de función interna no implica estabilidad de un SDK público.

## Formatos y versiones

| Contrato | Versión actual |
|---|---|
| Memoria clásica | schema 1 |
| Contexto universal clásico | formato v1 |
| Estado/API de extensiones EIP | v1 |
| Contexto portable EIP | v1 |
| Documentación UDP | edición 1, correspondiente al software 2.0.0 |

Las extensiones declaran permisos, dependencias y capacidades. Las versiones desconocidas se rechazan en lugar de ejecutarse por aproximación. [Esquemas y límites](/generated/reference/docs/platform/PLATFORM.html).

## Resultados y errores

La CLI devuelve JSON y códigos de salida. Errores de validación, permisos, rutas fuera de alcance o versiones incompatibles no deben interpretarse como entregas completadas. `platform run` distingue fallos de trabajos incompletos o pendientes de revisión; revisa su estado antes de cerrar una tarea.
