motor_reactor_realtime — Decisión y ejecución en tiempo real

Nota: Este archivo se escribe como README_LOCAL.md para evitar permisos de un README.md previo. Puede copiarse a README.md cuando se normalicen permisos.

Rol
- Decidir y orquestar ciclos de arbitraje triangular intra‑exchange con un presupuesto lógico < 3 ms.
- Considerar latencias, fees, slippage y estado de mercado antes de enviar órdenes.

Principios
- El cuello de botella real suele ser el matching del exchange; el motor debe minimizar todo lo demás.
- Despliegue cerca del exchange (VPS) para baja latencia.
- Lógica determinística y medible; nada suelto.

Entradas/Salidas
- Entradas: estructuras estandarizadas de refinery (orderbooks/tickers/rutas).
- Salidas: órdenes (sim/dry‑run/live), métricas de decisión, eventos a sentinel/event_hub.

Continuidad (`custom-codex-realtime`)
- `entorno.txt` | `fundaments-git.txt` | `history_git.txt`.

