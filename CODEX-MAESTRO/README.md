CODEX MAESTRO — Puntos de anclaje

Rol
- Definir directrices globales, modularidad y trazabilidad para internos.
- No cambiar infra/código fuera de acuerdos explícitos con Dominus.

Piezas clave del stack Binance
- AGENTS local (internos): `arbitraje-binance/AGENTS.md` (montado en contenedores como `/workspace/AGENTS.md`).
- Reglas de trabajo: `arbitraje-binance/codex-rules/rules` (montado como `/workspace/codex-rules/rules`).
- Volúmenes de continuidad: `custom-codex-<motor>/` por servicio.

Beacon Node (estado en simbiosis)
- No monta `AGENTS.md` ni `codex-rules` durante la fase de simbiosis para evitar acoplamientos cruzados.
- El compose de `beacon_node` queda en pausa “necesaria pero olvidada”: servirá como nodo común para unir y notificar eventos desde los sentinels de cada exchange.
- En el presente, se experimenta modularmente con sentinels por exchange; cada exchange puede exponer su propio flujo (posible WS), sin reglas Codex aplicadas al hub por ahora.

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
