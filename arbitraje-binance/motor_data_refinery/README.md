motor_data_refinery — Refinería de datos

Rol
- Traducir datos crudos del exchange a un formato filtrado y estandarizado apto para consumo inmediato por realtime.
- Aplicar filtros/normalizaciones que Dominus considera críticos (profundidad, precision, símbolos, fees, etc.).

Principios
- CCXT y librerías ayudan, pero siempre se valida manualmente por exchange. Cada exchange puede requerir mapeos y excepciones.
- Producto de salida listo para decidir en milisegundos: minimizar cómputo en realtime.
- Diseño modular para soportar futuros exchanges sin reescribir el core.

Entradas/Salidas
- Entradas: feeds/REST/WS del exchange (crudos), snapshots, incrementales.
- Salidas: estructuras normalizadas (ej. orderbooks, tickers, rutas A→B→C), emitidas en canal interno consumible por realtime.

Continuidad (`custom-codex-refinery`)
- `entorno.txt`: contexto del contenedor, visión y decisiones.
- `fundaments-git.txt`: convenciones Git locales.
- `history_git.txt`: cada cambio registrado con intención/resultado.

