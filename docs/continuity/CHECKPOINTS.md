# Checkpoints antes de cambios importantes

```console
python kit.py checkpoint create --label "Antes de migrar" --expected "Migrar sin perder pedidos ni romper el contrato actual"
python kit.py checkpoint list
python kit.py checkpoint show --id ID_DEVUELTO
python kit.py checkpoint verify --id ID_DEVUELTO
python kit.py checkpoint restore --id ID_DEVUELTO --destination ../recuperacion --dry-run
python kit.py checkpoint restore --id ID_DEVUELTO --destination ../recuperacion
```

Cada checkpoint se guarda en `project-memory/checkpoints/ID/` con metadatos JSON y `sources.zip`. Ambos son versionables. Captura fuentes seleccionadas y sus hashes, memoria estructurada, decisiones, etiqueta, resultado esperado, huella de código y reporte de pruebas disponible. No ejecuta pruebas automáticamente. `tests_fresh_and_passing=true` requiere un reporte no vacío, exitoso y con huella coincidente al capturar; los demás puntos siguen siendo recuperables, pero no se presentan como estados probados.

Los snapshots excluyen secretos detectados, binarios, bases de datos, archivos de más de 5 MB y carpetas ignoradas. Tienen límite total de 50 MB; no incluyen snapshots anteriores para evitar crecimiento recursivo. Consulte siempre `omitted`. Un snapshot parcial no garantiza recuperar todos los recursos de una aplicación. No sustituye un respaldo de producción.

`verify` comprueba metadatos, archivo comprimido, rutas y hashes individuales. No prueba la calidad del código ni la identidad del creador. Snapshots alterados, rutas fuera del destino y colisiones se rechazan antes de recuperar.

`restore` prepara los archivos en una carpeta nueva fuera del proyecto actual y agrega `project-memory/RECOVERY.json`. No sobrescribe archivos existentes, no hace reset ni elimina cambios actuales. Revisar diferencias, dependencias y exclusiones, ejecutar pruebas otra vez y decidir qué integrar. Aunque las pruebas fueran válidas al capturar, no se certifica el entorno de recuperación.

`orchestrate --apply` crea un checkpoint antes de añadir tareas. Una importación de contexto con sustitución crea otro antes de cambiar memoria. Para ediciones realizadas directamente por un IDE o asistente, el responsable debe llamar a `checkpoint create` antes del cambio: el kit no intercepta todos los editores ni crea snapshots de forma implícita fuera de sus comandos.
