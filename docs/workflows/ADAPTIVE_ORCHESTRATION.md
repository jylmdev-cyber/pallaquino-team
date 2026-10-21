# Orquestación adaptable

```console
python kit.py orchestrate --request "Documentar README"
python kit.py orchestrate --request "Agregar API de autenticación con base de datos SQL" --max-roles 4
python kit.py orchestrate --request "Corregir interacción" --file src/view.tsx --dry-run
python kit.py orchestrate --request "Agregar endpoint API" --apply --dry-run
python kit.py orchestrate --request "Agregar endpoint API" --apply
```

El planificador usa reglas locales explicables de [orchestration.json](../../configs/orchestration.json). No llama modelos ni consume tokens de inferencia. Clasifica el tipo de trabajo y combina señales del pedido y extensiones de archivos. `--kind` permite corregir la clasificación; las palabras clave no equivalen a una comprensión semántica completa. Los archivos de alcance son rutas relativas y no pueden salir del proyecto.

Una edición documental utiliza un solo perfil. Un pedido explícito de API con autenticación y SQL selecciona seguridad, datos, backend y QA con presupuesto de cuatro roles. El límite predeterminado es cuatro y se acepta entre uno y ocho; los roles no seleccionados se muestran con sus motivos en `deferred_roles`. Si el presupuesto deja fuera seguridad o QA requeridos por las reglas, el plan puede verse, pero aplicarlo falla hasta ampliar el presupuesto.

Sin `--apply`, solo devuelve un plan revisable. Al aplicarlo crea primero un checkpoint y luego un conjunto de tareas persistentes con responsables y criterios basados en sus contratos. La aceptación incluye el resultado solicitado y debe concretarse con el negocio antes de implementar funciones complejas. El registro `ai/plans/PLAN-ID.json` conserva el plan, las tareas y el checkpoint.

Aplicar el mismo plan dos veces reutiliza sus tareas sin duplicarlas, incluso si ya progresaron. Si se modifican sus contratos o se corrompe el recibo, falla para revisión. Para un incremento nuevo con los mismos roles, describir la nueva solicitud de forma concreta.

Las tareas se encadenan secuencialmente por defecto (`max_parallel=1`) para evitar escritores concurrentes y duplicación sobre el mismo alcance. `task ready` devuelve la primera pendiente con dependencias satisfechas; `agent brief` prepara el encargo. Los perfiles se ejecutan con asistentes/personas autorizados, no como procesos autónomos lanzados por el planificador. Planear auditoría no autoriza ejecutar Git; planear despliegue no autoriza actuar sobre producción.
