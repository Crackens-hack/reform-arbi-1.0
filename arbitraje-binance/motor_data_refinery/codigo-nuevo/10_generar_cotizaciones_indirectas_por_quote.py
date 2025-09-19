# ruta: /codigo/generar_cotizaciones_indirectas_por_quote_binance.py

import os
import sys
from pathlib import Path
import pandas as pd
from decimal import Decimal, getcontext, InvalidOperation

# Precisión máxima para cálculos financieros
getcontext().prec = 50

# Fix imports
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from codigo.config import EXCHANGE_ID  # type: ignore
base_dir = os.path.dirname(__file__)

# Rutas de entrada/salida (con subcarpeta binance)
path_pares = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', '1_quote_calculable_o_mixto.csv')
path_equiv = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'cotizaciones_directas_usdt', '2_a_usdt_equivale_base.csv')
path_salida = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', 'cotizaciones_indirectas_por_quote.csv')

# Validaciones de existencia
if not os.path.exists(path_pares):
    raise FileNotFoundError(f"❌ No se encontró el archivo de pares: {path_pares}")
if not os.path.exists(path_equiv):
    raise FileNotFoundError(f"❌ No se encontró el archivo de equivalencias USDT: {path_equiv}")

# Cargar archivos de entrada como strings para no perder precisión
df_pares = pd.read_csv(path_pares, dtype=str)
df_equiv = pd.read_csv(path_equiv, dtype=str)

# Crear diccionario: token → cuántas unidades del token rinde 1 USDT
# (del CSV 2_a_usdt_equivale_base.csv: columnas ['base', '1_usdt_equivale_base'])
usdt_equiv_dict = {}
for _, row in df_equiv.iterrows():
    token = str(row.get('base', '')).strip()
    val = str(row.get('1_usdt_equivale_base', '')).strip()
    if token and val and val.lower() != 'nan':
        try:
            usdt_equiv_dict[token] = Decimal(val)
        except (InvalidOperation, ValueError):
            # Ignorar valores inválidos
            continue

filas = []
for _, row in df_pares.iterrows():
    symbol = str(row.get('symbol', '')).strip()
    base = str(row.get('base', '')).strip()
    quote = str(row.get('quote', '')).strip()

    salida = {
        'symbol': symbol,
        'base': base,
        'quote': quote,
        # 1 USDT → cuántas unidades del quote (si disponible)
        '1_dolar_equivale_a_quote': ''
    }

    # Si hay precio directo del par en el CSV de entrada, lo usamos para el cálculo indirecto
    # (este CSV suele traer '1_base_equivale_x_quote' y '1_quote_equivale_x_base' cuando CCXT lo devolvió)
    raw_val = row.get('1_base_equivale_x_quote', '')
    sval = str(raw_val).strip()
    if sval and sval.lower() != 'nan':
        try:
            p_base_en_quote = Decimal(sval)
        except (InvalidOperation, ValueError):
            p_base_en_quote = None
    else:
        p_base_en_quote = None

    # Si conocemos cuántas unidades del quote rinde 1 USDT, anotamos y calculamos el precio indirecto en USDT
    if quote in usdt_equiv_dict:
        q_por_usdt = usdt_equiv_dict[quote]  # 1 USDT = q_por_usdt unidades de QUOTE
        salida['1_dolar_equivale_a_quote'] = str(q_por_usdt)

        # Si también tenemos el precio del par base/quote, computamos 1 BASE en USDT:
        # 1 BASE = (p_base_en_quote QUOTE) → en USDT = p_base_en_quote / (QUOTE por USDT)
        if p_base_en_quote is not None and q_por_usdt not in (None, 0):
            try:
                salida['1_base_equivale_usdt_indirecto'] = str(p_base_en_quote / q_por_usdt)
            except (InvalidOperation, ZeroDivisionError):
                salida['1_base_equivale_usdt_indirecto'] = ''
        else:
            salida['1_base_equivale_usdt_indirecto'] = ''
    else:
        # No hay equivalencia del quote con USDT en el diccionario
        salida['1_base_equivale_usdt_indirecto'] = ''
        # Podés loguear si querés:
        # print(f"⚠️ Quote sin equivalencia directa en USDT: {quote}")

    filas.append(salida)

# Guardar archivo final
df_final = pd.DataFrame(filas)
os.makedirs(os.path.dirname(path_salida), exist_ok=True)
df_final.to_csv(path_salida, index=False)

print("✅ Archivo generado:")
print(f"📄 {path_salida}")
