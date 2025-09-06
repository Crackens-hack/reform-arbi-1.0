CODEX MAESTRO — Puntos de anclaje

Rol
- Definir directrices globales, modularidad y trazabilidad para internos.
- No cambiar infra/código fuera de acuerdos explícitos con Dominus.

Piezas clave del stack Binance
- AGENTS local (internos): `arbitraje-binance/AGENTS.md` (montado en contenedores como `/workspace/AGENTS.md`).
- Reglas de trabajo: `arbitraje-binance/codex-rules/rules` (montado como `/workspace/codex-rules/rules`).
- Volúmenes de continuidad: `custom-codex-<motor>/` por servicio.

Event Hub (antes beacon_node)
- Servicio hub para recibir eventos de sentinels por exchange (WS) y notificar (p.ej., Telegram). Puede exponer control remoto (pausa/ajustes) si se decide.
- En simbiosis no montó `AGENTS.md`/`codex-rules` para evitar acoplamientos; hoy se lo documenta como pieza central de eventos.
- El código vive en `beacon_node/` y el binario/servicio se llama `event_hub`.

Trazabilidad (convención)
- Action-ID: `YYYYMMDD-HHMMSS-<rand4>` incluido en commits y archivos de continuidad.
- Historial de sesión: `custom-codex-<motor>/history_git.txt`.
- Fundamentos/decisiones: `custom-codex-<motor>/fundaments-git.txt`.

Orden sugerido al operar
1) Ver `AGENTS.md` y `codex-rules/rules`.
2) Fijar propósito y Action-ID.
3) Cambios estrictos en el ámbito del motor.
4) Commits con Action-ID + actualización de historia y fundamentos.
5) Registrar próximos pasos (opcional `NEXT.md`).

Nota
- El repo global está montado RO dentro de los contenedores. La escritura sucede solo en `<motor>` y `custom-codex-<motor>`.
