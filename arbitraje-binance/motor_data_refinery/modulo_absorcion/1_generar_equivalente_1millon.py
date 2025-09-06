# archivo: /modulo_absorcion/generar_equivalente_1millon.py

import os
import pandas as pd
import pymysql
from decimal import Decimal, getcontext

# Precisión interna muy alta
getcontext().prec = 50

# --- Config DB Kraken -------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# --- Rutas -------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
SRC = os.path.join(BASE_DIR, 'cotizaciones_equivalentes_1_usdt.csv')
DST_CSV = os.path.join(BASE_DIR, 'cotizaciones_equivalentes_1_millon_usdt.csv')
DST_YAML = os.path.join(BASE_DIR, 'cotizaciones_equivalentes_1_millon_usdt.yaml')

# --- Leer cotizaciones base -------------------------------------------
df = pd.read_csv(SRC, dtype=str)  # mantiene full-precision como texto

# --- Cargar precisión por símbolo desde kraken_funcional --------------
conn = pymysql.connect(**DB_CONFIG)
with conn.cursor() as cur:
    cur.execute("SELECT symbol, price FROM kraken_funcional")
    precisiones = {
        r['symbol']: Decimal(str(r['price'])).normalize().as_tuple().exponent * -1
        for r in cur.fetchall()
    }
conn.close()

# --- Función de truncado según precision ------------------------------
def a_1m_truncado(row):
    valor_1d = Decimal(row['1_dolar_equivale_a_quote'])
    bruto_1m = valor_1d * Decimal('1000000')
    decimales = precisiones.get(row['symbol'], 18)  # fallback: 18
    factor = Decimal('1').scaleb(-decimales)
    truncado = (bruto_1m // factor) * factor
    return str(truncado)

# --- Calcular columna truncada ----------------------------------------
df['1_millon_equivale_a_quote'] = df.apply(a_1m_truncado, axis=1)

# --- Guardar CSV final truncado ---------------------------------------
cols = ['symbol', 'base', 'quote', '1_dolar_equivale_a_quote', '1_millon_equivale_a_quote']
df[cols].to_csv(DST_CSV, index=False)

# --- Exportar versión tipo YAML (toda la tabla) ------------------------
with open(DST_YAML, 'w', encoding='utf-8') as f:
    for _, row in df.iterrows():
        f.write(f"- symbol    : {row['symbol']}\n")
        f.write(f"  base      : {row['base']}\n")
        f.write(f"  quote     : {row['quote']}\n")
        f.write(f"  1_usd     : {row['1_dolar_equivale_a_quote']}\n")
        f.write(f"  1m_usd    : {row['1_millon_equivale_a_quote']}\n")
        f.write("\n")
