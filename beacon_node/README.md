Event Hub — Recolector y notificador de eventos

Rol
- Recibir eventos desde los sentinels (WS) y reenviar notificaciones a Dominus (p.ej., Telegram).
- Exponer un canal de control remoto (pausa/ajustes) si se habilita.

Estado y nombres
- Directorio: `beacon_node/`.
- Servicio/binario: `event_hub` (ver Dockerfile y go.mod).

Integración
- Los motores/sentinels se conectan por WebSocket (variable `HUB_WS_URL`, por defecto `ws://event_hub:8080/ws`).
- No requiere montar `codex-rules-containers` durante simbiosis; hoy se documenta aquí su propósito.
