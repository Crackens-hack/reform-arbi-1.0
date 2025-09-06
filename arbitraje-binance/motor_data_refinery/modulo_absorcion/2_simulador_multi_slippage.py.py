# archivo: modulo_absorcion/simulador_multi_slippage.py

import os
import csv
import ccxt
from datetime import datetime

ARCHIVO_ENTRADA = 'cotizaciones_equivalentes_1_millon_usdt.csv'
ARCHIVO_SALIDA = 'snapshot_multi_slippage.csv'
EXCHANGE_ID = 'kraken'

# Slippages a evaluar (en porcentaje decimal)
SLIPPAGES = [0.001, 0.003, 0.005]  # 0.1%, 0.3%, 0.5%

exchange = getattr(ccxt, EXCHANGE_ID)({'enableRateLimit': True})

# Simula hasta donde se puede absorber sin superar el slippage permitido
def simular_absorcion(orderbook_asks, slippage_pct):
    if not orderbook_asks:
        return 0.0, 0, 0.0

    precio_inicial = orderbook_asks[0][0]
    precio_maximo = precio_inicial * (1 + slippage_pct)

    quote_usado = 0.0
    nivel_maximo_usado = 0
    for i, (precio, cantidad, *_ ) in enumerate(orderbook_asks):
        if precio > precio_maximo:
            break
        costo = precio * cantidad
        quote_usado += costo
        nivel_maximo_usado = i + 1
    return quote_usado, nivel_maximo_usado, precio_maximo

# Rutas absolutas
base_dir = os.path.dirname(__file__)
ruta_entrada = os.path.join(base_dir, ARCHIVO_ENTRADA)
ruta_salida = os.path.join(base_dir, ARCHIVO_SALIDA)

if not os.path.exists(ruta_entrada):
    raise FileNotFoundError(f"❌ Archivo no encontrado: {ruta_entrada}")

# Leer CSV de entrada
with open(ruta_entrada, 'r') as f:
    reader = csv.DictReader(f)
    datos = list(reader)

# Escribir CSV de salida
with open(ruta_salida, 'w', newline='') as f_out:
    writer = csv.writer(f_out)

    # Armar cabecera
    header = ['timestamp', 'symbol', 'quote', 'capital_simulado_quote']
    for s in SLIPPAGES:
        sufijo = f"{int(s*1000):03d}_slip"
        header += [
            f'capital_quote_max_{sufijo}',
            f'capital_usdt_equiv_{sufijo}',
            f'niveles_usados_{sufijo}',
            f'precio_limite_{sufijo}'
        ]
    writer.writerow(header)

    for fila in datos:
        symbol = fila['symbol']
        quote = fila['quote']
        try:
            capital_simulado = float(fila['1_millon_equivale_a_quote'])
            quote_por_1_usdt = float(fila['1_dolar_equivale_a_quote'])

            orderbook = exchange.fetch_order_book(symbol)
            asks = orderbook.get('asks', [])

            fila_out = [datetime.utcnow().isoformat() + 'Z', symbol, quote, capital_simulado]

            for s in SLIPPAGES:
                quote_usado, niveles, precio_max = simular_absorcion(asks, s)
                usdt_equiv = quote_usado / quote_por_1_usdt if quote_por_1_usdt > 0 else 0

                fila_out += [
                    round(quote_usado, 6),
                    round(usdt_equiv, 6),
                    niveles,
                    round(precio_max, 6)
                ]

            writer.writerow(fila_out)
            print(f"✅ {symbol} procesado correctamente.")

        except Exception as e:
            print(f"❌ Error procesando {symbol}: {e}")
