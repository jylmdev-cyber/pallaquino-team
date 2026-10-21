# Repositorio y autoría

Repositorio: [jylmdev-cyber/pallaquino-team](https://github.com/jylmdev-cyber/pallaquino-team).

Rama de entrega: `main`. La auditoría del remoto anterior a la publicación inicial confirmó ausencia de commits y referencias publicadas. Esta raíz corresponde a UASEK 2.0.0, con Engineering Intelligence Platform; los archivos temporales de preparación no forman parte de la entrega.

Identidad solicitada por el propietario para los commits de esta entrega:

- Nombre: Jimmy Lingan
- Correo: jylmdev@gmail.com

La identidad se configura localmente en este repositorio. Los campos author y committer se verifican antes de publicar. Los metadatos de un commit son declarativos; no constituyen una firma criptográfica ni prueban titularidad de una cuenta.

La publicación inicial 1.1 conservó su evidencia de [72 pruebas](../quality/evidence/tests-git-publication.json). La ampliación 2.0 incluye [120 pruebas](../quality/evidence/tests-2.0.0.json), instalación aislada y ZIP extraído; consultar el [reporte vigente](../quality/VALIDATION_REPORT.md). La [auditoría completa previa a EIP](../quality/evidence/git-audit-before-eip.json) confirmó `main` limpia y sincronizada, con el commit inicial existente. Los finales de línea de Windows se conservan para mantener las fuentes y snapshots existentes; la comprobación Git acepta CRLF y continúa verificando espacios sobrantes.

No versionar `.uasek/`, entornos virtuales, cachés, archivos `.env` reales ni resultados de construcción. Las fuentes de los checkpoints de `project-memory/checkpoints/` son parte de la continuidad y se conservan con su verificación de integridad. No es necesario publicar de nuevo los ZIP de distribución dentro del historial: el código y el empaquetador permiten generarlos.
