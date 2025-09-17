# Resumen de Arquitectura — Reform‑Arbi (Binance Lab)

## Visión General
- Propósito: motor de arbitraje triangular intra‑exchange con ICI (reinvierte cada ciclo), focalizado en Binance y modular para extender a otros exchanges.
- Ejes: datos limpios en milisegundos (refinería) → decisiones sub‑3 ms (realtime) → observabilidad (sentinel) → orquestación de eventos (event_hub).
- Meta operativa: detectar triadas con spread neto positivo tras fees y slippage, ejecutar de forma robusta, reinvertir, mantener control de riesgo.

## Módulos y Responsabilidades
- `arbitraje-binance/motor_data_refinery` (Refinería):
  - Unifica y filtra datos crudos; genera estructuras estables para consumo rápido.
  - Componentes: precalificador (estructuras y validaciones), generadores de cotizaciones directas/indirectas, módulo de absorción/triadas, exportador.
  - Entradas: feeds API/CCXT; Salidas: tablas/estructuras normalizadas listas para realtime.
- `arbitraje-binance/motor_reactor_realtime` (Realtime):
  - Ranking de triadas, evaluación en vivo de señal neta (fees + slippage + latencia), sizing (ICI) y disparo de órdenes.
  - Presupuesto lógico: < 3 ms por decisión; el cuello real es el matching del exchange.
- `arbitraje-binance/motor_sentinel` (Observabilidad):
  - Agrega métricas, eventos, anomalías y los envía por WS al hub.
  - Puede calcular indicadores de microestructura para pausar/alertar.
- `beacon_node` / servicio `event_hub` (Hub):
  - WebSocket server; recolecta eventos de sentinels (WS) y puede notificar (p.ej., Telegram) y/o exponer control remoto (pausa/ajustes).
- `arbitraje-binance/custom-codex-*` (Continuidad por motor):
  - Bitácoras operativas, fundamentos, entorno, historia de cambios; aislado por servicio para trazabilidad.

## Topología de Despliegue
- Físico/Red:
  - VPS/host cercano a la región de Binance; Docker Compose agrupa `motor_*` y `event_hub` en la misma red de Docker para latencias internas bajas.
  - `event_hub` escucha por defecto en `:8080` (ruta `/ws`).
- Contenedores:
  - Definidos en `arbitraje-binance/docker-compose.yml` (y `.env` en esa carpeta).
  - Volúmenes `custom-codex-<motor>` montados RW; monorepo global montado RO dentro de cada contenedor (seguridad).
- Interconexión:
  - `motor_sentinel` → WS → `event_hub`.
  - `motor_reactor_realtime` y `motor_data_refinery` comparten artefactos/archivos normalizados (rutas locales en volúmenes/dirs acordados).

## Flujo de Datos (End‑to‑End)
1) Ingesta y Normalización (Refinería):
   - Generación/validación de esquemas mínimos por exchange y símbolos.
   - Cálculo de cotizaciones directas (USDT→X) y derivación de indirectas (USDT→A→B, A/B) con control de coherencia.
   - Módulo de absorción cuantifica liquidez utilizable, simula slippage multi‑escenario y produce snapshot/triadas ordenadas por “capacidad de absorción”.
2) Exportación a Realtime:
   - Tablas/artefactos “producto listo” (p.ej., CSV/estructuras serializadas) con triadas candidatas y métricas agregadas.
3) Decisión y Ejecución (Realtime):
   - Lee “producto listo”, evalúa spread neto esperado (fees y slippage), aplica margen de seguridad, rankea y decide enviar orden.
   - Calcula tamaño (ICI) sujeto a límites de liquidez/absorción y reglas de riesgo.
4) Observabilidad y Control:
   - Eventos (señal, activación, éxito/fallo parcial, anomalías, pausas) salen vía `motor_sentinel` → `event_hub`.
   - Notificaciones externas opcionales y control remoto (pausa/overrides) vía `event_hub` si se habilita.

## Interfaces y Contratos
- WebSocket `event_hub`:
  - URL: `ws://event_hub:8080/ws`; requiere header `X-Stack-ID` (identifica el emisor).
  - Implementación en `beacon_node/cmd/event_hub/main.go` (usa `gorilla/websocket`).
  - Contrato de mensajes (recomendado): JSON `{type, ts, level, payload, stack_id}`.
- Artefactos refinería → realtime:
  - Contrato: tablas con triadas y métricas (spread bruto, fees agregadas, absorción estimada, slippage esperado, net_spread_expected).
  - Rutas y esquema final se confirman con Dominus; la refinería ya produce múltiples CSV y scripts de consolidación.

## Datos y Esquemas (Mínimos Efectivos)
- Nivel cotización/símbolo:
  - `symbol`, `base`, `quote`, `bid`, `ask`, `bid_qty`, `ask_qty`, `ts`, `fees_taker`, `min_qty`, `step_size`.
- Nivel triada:
  - `leg1`, `leg2`, `leg3` (símbolos y dirección), `gross_spread`, `fees_total`, `slippage_expected`, `net_spread_expected`, `absorption_cap`, `latency_budget`, `safety_margin`.
- Notas:
  - En el repo hay ejemplos de esquemas/plantillas para Kraken que sirven de referencia, aunque el foco es Binance.

## Rendimiento y Latencia
- Presupuesto:
  - Lógica de decisión: < 3 ms por triada candidata (excluye red/exchange).
  - Bottleneck real: matching de órdenes en exchange y red.
- Estrategias:
  - Precomputar triadas y métricas en refinería para que realtime solo consulte y evalúe.
  - Minimizar parseo/IO en realtime (estructuras compactas, en memoria si es viable).
  - Colocar instancias cerca de endpoints de Binance (zona/POP adecuados).

## Riesgos y Salvaguardas
- Riesgos: slippage por microestructura, ejecución parcial, latencia variable, fees efectivas, cambios de lote/tick.
- Salvaguardas:
  - Margen de seguridad sobre spread neto esperado.
  - Límites dinámicos de tamaño según `absorption_cap`.
  - Reglas de pausa automatizada ante volatilidad o lag.
  - Gestión de fallos parciales (reintentos o hedge, según se defina).

## Observabilidad y Control
- `motor_sentinel`:
  - Envía eventos claves: señal, activación, confirmación, error, condiciones de pausa, métricas agregadas.
  - Código base en `arbitraje-binance/motor_sentinel/main.py` y `calc.py`.
- `event_hub`:
  - WS server con `/ws` y `/healthz`; logging por cliente; ver `beacon_node/cmd/event_hub/main.go`.
- Métricas sugeridas:
  - Tasa de señales válidas, ratio de activación, beneficio por ciclo, tiempos de ida/vuelta, slippage observado vs. esperado, pausas y sus causas.

## Configuración y Parámetros
- Archivos:
  - `arbitraje-binance/.env`: credenciales y parámetros por stack.
  - `arbitraje-binance/docker-compose.yml`: servicios, redes, volúmenes.
- Variables clave:
  - `HUB_WS_URL` en motores para WS del hub, `PORT` en hub.
  - Parámetros de fees/limites/ICI en runtime (ideal: centralizarlos en un archivo de configuración del stack).

## Escalabilidad y Extensión
- Horizontal:
  - Paralelizar evaluación de triadas (sharding por quote/base).
  - Múltiples instancias realtime y sentinel por exchange/mercado.
- Cross‑exchange:
  - La refinería modulariza mapeos por exchange; añadir mapeos/esquemas y listas de símbolos por nuevo exchange.
  - Evitar acoplar heurísticas a un solo exchange; parametrizar fees/ticks/min_qty.

## Estructura del Repo (Mapa Clave)
- `README.md`: visión y arquitectura global.
- `arbitraje-binance/docker-compose.yml` y `.env`: stack de Binance.
- `arbitraje-binance/motor_data_refinery/`:
  - `README.md`, `entrypoint.sh`, `requirements.txt`.
  - `precalificador_primario/codigo/*`: generación de esquemas, validaciones, cotizaciones directas/indirectas.
  - `modulo_absorcion/*`: simuladores de slippage, capacidad de absorción, generación de triadas y exportación.
  - `codigo/6a_generar_cotizador_directo_desde_ccxt.py`: cotizador directo desde CCXT.
- `arbitraje-binance/motor_reactor_realtime/`: lógica de decisión/ejecución (estructura lista para profundizar).
- `arbitraje-binance/motor_sentinel/`: `main.py`, `Dockerfile`, `entrypoint.sh`, dev scripts.
- `beacon_node/cmd/event_hub/main.go`: WS Hub (Go).
- `arbitraje-binance/custom-codex-*`: `entorno.txt`, `fundaments-git.txt`, `history_git.txt`, notas/intención.

## Ciclo Operativo
- Pre‑market:
  - Generar/validar “producto listo” en refinería; calibrar slippage/fees y límites.
- En vivo:
  - Realtime consume artefactos, rankea triadas, evalúa señal neta, ejecuta y reporta.
  - Sentinel monitorea y notifica; `event_hub` agrega y reemite fuera si procede.
- Post‑operación:
  - Auditar resultados vs. esperado, recalibrar slippage/seguridad, actualizar artefactos y supuestos.

## Extensiones Inmediatas Recomendadas
- Contrato de mensajes JSON en `event_hub` y `motor_sentinel`.
- Definir esquema único “producto listo” (ruta y columnas) para `realtime`.
- Pseudocódigo/estado de `motor_reactor_realtime`: ranking, criterio de entrada, sizing ICI, ejecución.
- Script de backtest mínimo usando artefactos exportados por refinería.

