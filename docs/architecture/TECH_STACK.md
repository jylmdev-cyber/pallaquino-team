# Stack del kit

Verificación documental: 2026-10-21. Ejecución local: Python 3.12.10 y Git 2.55.0.windows.5. Esto registra versiones observadas, no afirma que sean las últimas ni recomienda sus parches específicos para producción.

| Tecnología | Versión/compatibilidad | Tipo | Justificación | Soporte |
|---|---|---|---|---|
| Python | >=3.11; probado 3.12.10 | Serie estable, biblioteca estándar | argparse, tomllib, unittest, urllib y zipfile sin dependencias runtime | Consultar ciclo oficial; rama 3.12 en fase de seguridad |
| Git | Observada 2.55.0.windows.5; comandos básicos | Herramienta opcional | Inspección local autorizada | Verificar mantenimiento de la distribución instalada |
| Framework | No requerido | No aplica | CLI modular | No aplica |
| Base de datos | JSON/Markdown schema 1 | Archivos versionables | Portabilidad y revisión de cambios | Contrato del kit |
| Build | setuptools>=68 | Solo instalación opcional | Empaquetado del CLI y recursos | Versión resuelta depende del entorno; no fijada como dependencia de ejecución |

Fuentes oficiales: [versiones Python](https://devguide.python.org/versions/), [PEP 693](https://peps.python.org/pep-0693/), [documentación argparse](https://docs.python.org/3/library/argparse.html), [Git](https://git-scm.com/docs). Python 3.12 recibe correcciones de seguridad hasta aproximadamente octubre de 2028 según su calendario; actualizar el parche o usar una serie estable mantenida antes de desplegar.

El kit no selecciona stack de negocio automáticamente. `stack --online` verifica metadatos en PyPI o npm y devuelve fecha/fuente, pero compatibilidad, soporte y avisos requieren revisión adicional.
