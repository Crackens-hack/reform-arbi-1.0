motor_sentinel — Observabilidad y eventos

Rol
- Vigilar señales clave (spreads, errores, estados) y enviarlas a Event Hub vía WebSocket.
- Formatear logs/eventos para notificación (p.ej., Telegram) y para auditoría interna.

Principios
- Simplicidad y robustez: capturar lo importante sin bloquear a realtime.
- Extensible por exchange; cada sentinel puede tener particularidades mínimas.

Entradas/Salidas
- Entradas: métricas internas, logs del motor, hooks de ejecución.
- Salidas: eventos WS a `event_hub`, logs normalizados.

Continuidad (`custom-codex-sentinel`)
- `entorno.txt` | `fundaments-git.txt` | `history_git.txt`.

