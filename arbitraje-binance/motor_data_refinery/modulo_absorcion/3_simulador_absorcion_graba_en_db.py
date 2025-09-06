# archivo: modulo_absorcion/simulador_absorcion_db.py

import os
import csv
import ccxt
import pymysql
from datetime import datetime

# --- Configuración de DB usando variables de entorno DB2_* ---
DB_CONFIG = {
    "host": os.getenv("DB2_HOST"),
    "user": os.getenv("DB2_USER"),
    "password": os.getenv("DB2_PASSWORD"),
    "database": os.getenv("DB2_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

# --- Parámetros generales ---
ARCHIVO_ENTRADA = os.path.join(os.path.dirname(__file__), 'cotizaciones_equivalentes_1_millon_usdt.csv')
EXCHANGE_ID = 'kraken'
SLIPPAGE = 0.003  # 0.3%
TABLE_SNAPSHOT = 'absorcion_snapshot_global'
PREFIX = 'absorcion_'

# --- Simula absorción sin superar el slippage tolerado ---
def simular_absorcion(orderbook_asks, slippage_pct):
    if not orderbook_asks:
        return 0.0, 0, 0.0
    precio_inicial = orderbook_asks[0][0]
    precio_max = precio_inicial * (1 + slippage_pct)
    quote_usado, niveles_usados = 0.0, 0
    for i, (precio, cantidad, *_ ) in enumerate(orderbook_asks):
        if precio > precio_max:
            break
        quote_usado += precio * cantidad
        niveles_usados = i + 1
    return quote_usado, niveles_usados, precio_max

# --- Validación del archivo de entrada ---
if not os.path.exists(ARCHIVO_ENTRADA):
    raise FileNotFoundError(f"❌ No se encontró el archivo de entrada: {ARCHIVO_ENTRADA}")

# --- Conexión a DB ---
conn = pymysql.connect(**DB_CONFIG)
cur = conn.cursor()

try:
    # --- Leer archivo CSV ---
    with open(ARCHIVO_ENTRADA, 'r') as f:
        reader = csv.DictReader(f)
        datos = list(reader)

    # --- Crear tabla snapshot (global) ---
    cur.execute(f"DROP TABLE IF EXISTS {TABLE_SNAPSHOT}")
    cur.execute(f"""
        CREATE TABLE {TABLE_SNAPSHOT} (
            timestamp_utc DATETIME,
            symbol VARCHAR(50),
            quote VARCHAR(20),
            capital_simulado_quote DECIMAL(32,12),
            capital_quote_max_003_slip DECIMAL(32,12),
            capital_usdt_equiv_003_slip DECIMAL(32,12),
            niveles_usados_003_slip INT,
            precio_limite_003_slip DECIMAL(32,12)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # --- Inicializar exchange y timestamp global ---
    exchange = getattr(ccxt, EXCHANGE_ID)({'enableRateLimit': True})
    now = datetime.utcnow().replace(microsecond=0)

    # --- Loop por símbolo ---
    for fila in datos:
        try:
            symbol = fila['symbol']
            quote = fila['quote']
            capital_simulado = float(fila['1_millon_equivale_a_quote'])
            quote_por_1_usdt = float(fila['1_dolar_equivale_a_quote'])

            orderbook = exchange.fetch_order_book(symbol)
            asks = orderbook.get('asks', [])

            quote_usado, niveles, precio_max = simular_absorcion(asks, SLIPPAGE)
            usdt_equiv = quote_usado / quote_por_1_usdt if quote_por_1_usdt > 0 else 0

            # --- Insertar en snapshot global ---
            cur.execute(f"""
                INSERT INTO {TABLE_SNAPSHOT} (
                    timestamp_utc, symbol, quote, capital_simulado_quote,
                    capital_quote_max_003_slip, capital_usdt_equiv_003_slip,
                    niveles_usados_003_slip, precio_limite_003_slip
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                now, symbol, quote, capital_simulado,
                quote_usado, usdt_equiv, niveles, precio_max
            ))

            # --- Insertar en tabla por símbolo ---
            tabla_simbolo = f"{PREFIX}{symbol.lower().replace('/', '_').replace(' ', '').replace('.', '')}"
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {tabla_simbolo} (
                    timestamp_utc DATETIME,
                    capital_simulado_quote DECIMAL(32,12),
                    capital_quote_max_003_slip DECIMAL(32,12),
                    capital_usdt_equiv_003_slip DECIMAL(32,12),
                    niveles_usados_003_slip INT,
                    precio_limite_003_slip DECIMAL(32,12)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute(f"""
                INSERT INTO {tabla_simbolo} (
                    timestamp_utc, capital_simulado_quote,
                    capital_quote_max_003_slip, capital_usdt_equiv_003_slip,
                    niveles_usados_003_slip, precio_limite_003_slip
                ) VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                now, capital_simulado,
                quote_usado, usdt_equiv, niveles, precio_max
            ))

            print(f"✅ {symbol} insertado en snapshot y tabla histórica")

        except Exception as e:
            print(f"❌ Error procesando símbolo {fila.get('symbol', '?')}: {e}")

finally:
    cur.close()
    conn.close()
    print("✅ Conexión cerrada. Script finalizado correctamente.")
