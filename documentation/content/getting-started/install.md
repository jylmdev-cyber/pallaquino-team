# Instalar y comprobar

## Requisitos

El núcleo requiere Python 3.11 o superior y utiliza la biblioteca estándar. La validación local registrada se realizó en Windows con Python 3.12.10. Git se necesita para obtener el repositorio o ejecutar una auditoría autorizada. El portal añade Node **24.22.x** y npm; no los necesita la CLI Python.

## Windows

```powershell
git clone https://github.com/jylmdev-cyber/pallaquino-team.git
cd pallaquino-team
py -3 kit.py doctor
py -3 kit.py --help
```

Si Python está disponible como `python`, úsalo en lugar de `py -3` en los ejemplos siguientes. También puedes extraer la distribución ZIP y entrar en su carpeta raíz.

## Linux y macOS

```sh
git clone https://github.com/jylmdev-cyber/pallaquino-team.git
cd pallaquino-team
python3 kit.py doctor
python3 kit.py --help
```

Son instrucciones de instalación reproducibles; el reporte distingue las plataformas realmente ejecutadas de las pendientes. No se declara validación Linux/macOS por incluir estos comandos.

## Crear un proyecto

```console
python kit.py init --destination ../mi-proyecto --name "Mi proyecto" --template inventory
python kit.py --root ../mi-proyecto status
python kit.py --root ../mi-proyecto platform init
```

El destino nuevo evita sobrescribir un proyecto existente. EIP se activa por proyecto y empieza en modo supervisado. Después de activarlo, también los comandos anteriores respetan su política.

## Portal local

```console
python tools/docs_manager.py generate
cd documentation/portal
npm ci --ignore-scripts
npm run dev
```

Abre la URL local indicada por VitePress. Para validar el build, vuelve a la raíz:

```console
python tools/docs_manager.py validate
python tools/docs_manager.py build
```

## Configuración y variables

| Variable | Uso | Valor predeterminado |
|---|---|---|
| `GITHUB_REPOSITORY` | Propietario/repositorio del portal | `jylmdev-cyber/pallaquino-team` |
| `DOCS_BASE` | Ruta pública, siempre con `/` inicial y final | `/pallaquino-team/` |
| `DOCS_ORIGIN` | Origen HTTPS sin ruta, para sitemap | `https://jylmdev-cyber.github.io` |
| `UDP_PAGES_ENABLED` | Variable de GitHub que habilita el job de publicación | Ausente: publicación deshabilitada |

El portal no requiere credenciales ni servicios externos de búsqueda. No crear archivos `.env` con claves para generar documentación. El [manual del portal](/generated/reference/documentation/PORTAL_MANUAL.html) explica configuración de GitHub y dominio personalizado.

## Verificación y errores frecuentes

`doctor` debe mostrar Python compatible y memoria existente. `status` muestra las tareas; `--help` presenta los comandos. Si npm no existe o no cumple la versión declarada, instala el runtime antes de construir. Si una carpeta destino existe, utiliza una nueva. Consulta [errores comunes](/troubleshooting/common.html).
