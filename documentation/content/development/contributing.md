# Contribuir

## Preparar un cambio revisable

1. Delimita requisito, responsable y criterios de aceptación.
2. Crea un checkpoint antes de cambios importantes.
3. Implementa en el alcance asignado y añade pruebas de comportamiento cuando corresponda.
4. Actualiza las fuentes documentales afectadas.
5. Ejecuta las comprobaciones locales y adjunta evidencia.

```console
python kit.py test
python tools/docs_manager.py generate
python tools/docs_manager.py validate
python tools/docs_manager.py build
```

## Dónde editar

Las guías manuales viven en `documentation/content/`. Los contratos de agentes se mantienen en `configs/agents.json`; las skills en `skills/`; los sistemas de referencia en `templates/systems/` y su catálogo. Las páginas `generated/` son derivadas y no deben editarse directamente.

No incluyas memoria privada, aprobaciones, logs locales, credenciales ni archivos `.env` en la documentación pública. La generación usa una lista explícita de fuentes y rechaza patrones de posibles secretos; la revisión humana sigue siendo necesaria.

## Revisión y publicación

Las pull requests ejecutan validación y build, con permisos de lectura. No publican el portal. Publicar requiere habilitación del propietario y el entorno `github-pages`; este trabajo deja ese despliegue deshabilitado.

El propietario solicitó que los commits autorizados de esta entrega usen Jimmy Lingan y su correo declarado. Configurar metadatos no sustituye una firma ni concede permiso de publicación. [Repositorio y autoría](/generated/reference/docs/operations/REPOSITORY.html).

## Accesibilidad

Usa encabezados jerárquicos, enlaces descriptivos, tablas simples, texto alternativo y navegación con teclado. El objetivo es WCAG 2.2 AA; las comprobaciones locales no equivalen a una certificación completa. Evita animaciones y recursos remotos innecesarios.
