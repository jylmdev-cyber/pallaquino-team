# Plan de migración

Antes de ejecutar: registrar esquema origen/destino, versión, volumen, ensayo de respaldo/recuperación y aprobación para cambios destructivos.

Secuencia sugerida: expandir esquema → adaptar lectores/escritores → migrar lotes idempotentes → reconciliar conteos y restricciones → retirar compatibilidad cuando no queden consumidores anteriores.

Criterio de corte: integridad verificada y umbral de bloqueo acordado. Documentar reversión o reparación hacia adelante y responsable de detener el corte.
