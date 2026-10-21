# Repositorio y autoría

Repositorio: [jylmdev-cyber/pallaquino-team](https://github.com/jylmdev-cyber/pallaquino-team).

Rama de entrega inicial: `main`. La auditoría del remoto anterior a la publicación confirmó ausencia de commits y referencias publicadas. El contenido de esta raíz corresponde al kit UASEK 1.1.0; los archivos temporales de preparación no forman parte de la entrega.

Identidad solicitada por el propietario para los commits de esta entrega:

- Nombre: Jimmy Lingan
- Correo: jylmdev@gmail.com

La identidad se configura localmente en este repositorio. Los campos author y committer se verifican antes de publicar. Los metadatos de un commit son declarativos; no constituyen una firma criptográfica ni prueban titularidad de una cuenta.

Validación previa a la publicación: [72 pruebas](../quality/evidence/tests-git-publication.json), incluyendo el ajuste final de la línea vacía de `pyproject.toml`. Los finales de línea de Windows se conservan para mantener las fuentes y snapshots existentes; la comprobación Git acepta CRLF y continúa verificando espacios sobrantes.

No versionar `.uasek/`, entornos virtuales, cachés, archivos `.env` reales ni resultados de construcción. Las fuentes de los checkpoints de `project-memory/checkpoints/` son parte de la continuidad y se conservan con su verificación de integridad. No es necesario publicar de nuevo los ZIP de distribución dentro del historial: el código y el empaquetador permiten generarlos.
