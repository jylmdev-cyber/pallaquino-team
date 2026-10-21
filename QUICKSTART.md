# Inicio rápido

Para seleccionar roles sin invocar modelos: `python kit.py orchestrate --request "Agregar endpoint API"`. Añada `--apply` para crear tareas y un checkpoint previo. Antes de una edición importante hecha fuera del kit, use `python kit.py checkpoint create --label "Antes del cambio" --expected "Resultado observable"`. Véase [continuidad 1.1](docs/continuity/CONTEXT_FORMAT.md).

Requiere Python 3.11+; se comprobó localmente con Python 3.12.10 en Windows. Git es opcional salvo para `audit`. Extraiga el ZIP y abra una terminal dentro de `UNIVERSAL-AI-SOFTWARE-KIT`.

```console
python kit.py doctor
python -m unittest discover -s tests -v
python kit.py catalog
python kit.py init --destination ../demo-inventario --name "Inventario" --template inventory
python kit.py --root ../demo-inventario task add --title "Acordar reglas" --agent business-analyst --acceptance "Negocio valida movimientos y excepciones"
python kit.py --root ../demo-inventario task ready
python kit.py --root ../demo-inventario agent brief --task T0001
```

Abra el archivo de encargo devuelto, entréguelo a su asistente y revise sus artefactos. No cierre la tarea solo porque el modelo diga que terminó. Tras revisar y guardar evidencia dentro del proyecto:

```console
python kit.py --root ../demo-inventario task update --id T0001 --status done --evidence docs/reglas-aprobadas.md
python kit.py --root ../demo-inventario provider switch --provider claude
python tools/context_manager.py export --root ../demo-inventario
```

El comando de cierre requiere que `docs/reglas-aprobadas.md` exista; los dos últimos generan `project-memory/AI_HANDOFF.md`. Abra ese archivo en el asistente destino junto con los archivos del proyecto necesarios. Revise su contenido antes de compartirlo.

Para continuar un proyecto existente, use `--root` con su carpeta. Si no tiene memoria, haga inventario con `analyze` y acuerde la reconstrucción. `python kit.py init --destination ../existente --name "Sistema existente" --existing` incorpora solo memoria sin reemplazar archivos del proyecto. El [manual](docs/user-manual/MANUAL.md) describe la auditoría autorizada y la incorporación segura.
