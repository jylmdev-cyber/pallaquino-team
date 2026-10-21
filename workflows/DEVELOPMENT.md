# Protocolo de desarrollo y continuidad

Antes de cambios importantes, crear checkpoint con etiqueta y resultado esperado. `orchestrate --apply` e importación sustitutiva lo hacen automáticamente para sus propias mutaciones. Para cambios externos de código, el responsable ejecuta el comando antes de editar. Usar `orchestrate` para seleccionar un equipo proporcionado al alcance, revisar roles diferidos y criterios, y `context export` para continuidad universal sin instrucciones internas de proveedores.

Al iniciar con `python kit.py`, mostrar el saludo y las siete alternativas sin escribir archivos. El asistente espera selección antes de implementar un proyecto de negocio.

Para proyecto nuevo preguntar progresivamente por nombre, problema, usuarios y flujo principal. Después aclarar plataforma, integración, restricciones, seguridad y despliegue cuando afecten decisiones. Proponer opciones si no se conoce una respuesta y registrar supuestos. La construcción de este kit fue solicitada explícitamente; el protocolo se aplica a los proyectos que lo utilizan.

Para proyecto existente confirmar ruta y pedir auditoría: completa, rápida, rechazar o sin repositorio. `audit --authorize` solo tras autorización humana; este flag no es una solicitud ni reemplaza la respuesta del usuario. El rechazo se registra como decisión de memoria. Inventario mínimo no ejecuta Git ni código.

Fases adaptables: descubrimiento → auditoría autorizada si corresponde → requisitos → investigación del stack → arquitectura → planificación → implementación incremental → pruebas → seguridad → validación funcional → documentación → preparación de entrega → memoria y handoff → mantenimiento.

El coordinador consulta `task ready`, genera `agent brief` y entrega el encargo al asistente o persona correspondiente. Dependencias deben existir antes de agregarse al encargo. No se inicia tarea con dependencias incompletas. No se necesita un rol nuevo para cada cambio menor.

Resultados siguen RESULT_CONTRACT.json y se guardan dentro del proyecto. `agent validate --result ruta.json` comprueba estructura y referencias; el coordinador revisa contenido, aceptación y fallos antes de `task update --status done --evidence archivo`. No hay cierre automático basado en afirmaciones de un modelo.

Actualizar memoria con hechos y decisiones, ejecutar `docs` para vistas derivadas y `handoff` para continuidad. Un checkpoint es referencia de un estado validado, no un sustituto de las pruebas. Cambios relevantes de arquitectura se justifican y acuerdan; producción, publicación y operaciones destructivas requieren autorización explícita de su plan concreto.
