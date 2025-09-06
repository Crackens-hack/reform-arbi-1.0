Reform‑Arbi — Motor de Arbitraje Triangular (Binance Lab)

Resumen
- Objetivo: motor de arbitraje triangular intra‑exchange (USDT → A → B → USDT; variantes con USDC) con ICI (Interés Compuesto Inmediato) según la visión y diseño de Dominus: cada ciclo reinvierte inmediatamente el resultado para crecer de forma exponencial (~1% diario sostenido como meta).
- Tesis de Dominus: el ICI tiene máximo potencial si se arriesga el capital completo, pero con control estricto en tiempo real. Por eso la arquitectura pone especial énfasis en datos limpios (refinería) y decisiones milimétricas (realtime).
- Estado: fase post‑simbiosis. La simbiosis definió reglas, volúmenes custom‑codex por motor y la coordinación Maestro ↔ Internos.
- Alcance actual: laboratorio en Binance, sujeto de prueba y a la vez base de negocio; se diseña modular para extender a más exchanges.

Arquitectura (visión rápida)
- Monorepo único, organizado por servicios y motores.
- Stack Binance (directorio `arbitraje-binance/`):
  - Motores: `motor_data_refinery` (refinería de datos), `motor_reactor_realtime` (decisión/ejecución), `motor_sentinel` (observabilidad y eventos).
  - Volúmenes de continuidad por motor: `custom-codex-<motor>/`.
  - Compose y tooling local para desarrollo.
- Event Hub (antes “beacon_node”): servicio hub para recolectar eventos de sentinels (vía WebSocket) y notificar a Dominus (p.ej. Telegram). Puede servir también para acciones remotas (pausa/parámetros) si se habilita.
- Reglas y documentación:
  - Maestro: `CODEX-MAESTRO/rules.md` (dirección global post‑simbiosis).
  - Internos (contenedores): `codex-rules/rules.md` (constitución mínima montada RO).
  - Puntero interno por stack: `arbitraje-binance/AGENTS.md`.

Flujo de trabajo
- Codex Maestro (externo):
  1) Confirmar rol y leer `CODEX-MAESTRO/rules.md`.
  2) Limar y cerrar el objetivo junto a Dominus; registrar en `CODEX-MAESTRO/objetivo.md`.
  3) Derivar la intención a README por carpeta (mapa de “cómo y dónde está todo”).
- Codex internos (por contenedor):
  1) Leer `codex-rules/rules.md` montado en el contenedor.
  2) Trabajar solo dentro de `custom-codex-<motor>/` y `<motor>`.
  3) Mantener `entorno.txt`, `fundaments-git.txt`, `history_git.txt` al día (commits atómicos y frecuentes).

Motores y responsabilidades
- motor_data_refinery (Refinería):
  - Traduce datos crudos a un formato filtrado y estandarizado que los servicios de realtime puedan entender de manera uniforme.
  - Usa CCXT y herramientas afines, pero Dominus siempre inspecciona y valida manualmente el formato por exchange. No es push‑button: cada exchange puede requerir mapeos/ajustes propios.
  - Objetivo: entregar un “producto listo” para consumo en milisegundos, filtrando lo que Dominus sabe que debe filtrarse, con máxima modularidad y escalabilidad.
- motor_reactor_realtime (Realtime):
  - Toma decisiones programáticas ultrarrápidas (< 3 ms de presupuesto lógico) para arbitraje triangular intra‑exchange.
  - Considera múltiples factores medibles; asume que el mayor cuello de botella real será el matching de órdenes en el exchange.
  - Pensado para ejecutarse en VPS cerca de los exchanges para minimizar latencias.
- motor_sentinel (Observabilidad):
  - Observa, agrega y envía eventos/indicadores a Event Hub (WS). Ejemplos: spreads extremos, errores, señales operativas.
  - También puede recolectar logs y formatearlos para notificación.
- event_hub (Hub de eventos):
  - Recolector de señales desde sentinels, emisor de notificaciones a Dominus (p.ej., Telegram) y canal de control remoto (pausa/ajustes) si se activa.
  - En el código actual, vive en `beacon_node/` pero el servicio se llama `event_hub` (renombre efectivo en documentación; sin cambios en compose por ahora).

Arranque rápido (desarrollo local)
1) Requisitos: Docker + Docker Compose, archivo `.env` en `arbitraje-binance/` (ya existe un ejemplo base en repo).
2) Levantar servicios (desde `arbitraje-binance/`):
   - `docker-compose up -d`
3) Entrar a un motor (ejemplos):
   - `docker compose exec motor_data_refinery bash`
   - `docker compose exec motor_reactor_realtime bash`
   - `docker compose exec motor_sentinel bash`
4) Dentro del contenedor: seguir `AGENTS.md` (puntero) → `codex-rules/rules.md` y crear/verificar `custom-codex-<motor>/entorno.txt`.

Notas y alcance operativo
- Binance es el sujeto máximo de prueba y la base del negocio, pero el diseño es modular para sumar más exchanges (Kraken, Bybit, etc.).
- En el futuro se añadirá un mini‑contenedor para medir latencias de red del VPS hacia distintos exchanges y decidir qué desplegar.
- Git y Codex sirven para modularización y trazabilidad durante desarrollo; en operación productiva, la prioridad será seguridad/latencia y no depender de estas herramientas en runtime.

Estructura esencial del repo
- `arbitraje-binance/`: compose, motores, volúmenes custom y soporte de entorno para Binance.
- `arbitraje-binance/motor_*`: código por motor (refinery, realtime, sentinel).
- `arbitraje-binance/custom-codex-*`: continuidad por motor (bitácoras y reglas locales de Git).
- `CODEX-MAESTRO/`: guías del Maestro y coordinación global.
- `codex-rules/`: reglas canónicas montadas en contenedores (solo lectura).

Privacidad y seguridad
- Todo el contenido es privado; no se comparte fuera del entorno controlado.
- Escritura únicamente dentro del ámbito permitido de cada motor/volumen.

Siguientes pasos sugeridos
- Maestro: crear/llenar `CODEX-MAESTRO/objetivo.md` con el objetivo cerrado y criterios de éxito.
- Internos: completar `entorno.txt` y mantener `history_git.txt` y `fundaments-git.txt` con cada cambio.
- Documentación: agregar README específicos en cada carpeta relevante siguiendo el mapa global.
