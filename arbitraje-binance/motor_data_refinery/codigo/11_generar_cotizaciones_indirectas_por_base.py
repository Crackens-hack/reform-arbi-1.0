# ruta: /codigo/generar_cotizaciones_indirectas_por_base_binance.py

import os
import pandas as pd
from decimal import Decimal, getcontext, InvalidOperation

# Precisión alta para evitar errores de redondeo
getcontext().prec = 50

EXCHANGE_ID = "binance"
base_dir = os.path.dirname(__file__)

# Rutas (con subcarpeta binance)
path_base_solo = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', '2_solo_base_calculable.csv')
path_usdt_equiv = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'cotizaciones_directas_usdt', '2_a_usdt_equivale_base.csv')
path_salida     = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', 'cotizaciones_indirectas_por_base.csv')

# Validaciones de existencia
if not os.path.exists(path_base_solo):
    raise FileNotFoundError(f"❌ No se encontró: {path_base_solo}")
if not os.path.exists(path_usdt_equiv):
    raise FileNotFoundError(f"❌ No se encontró: {path_usdt_equiv}")

# Cargar datos como strings para preservar precisión
df_base_solo = pd.read_csv(path_base_solo, dtype=str)
df_equiv     = pd.read_csv(path_usdt_equiv, dtype=str)

# Diccionario: base → unidades de BASE que rinde 1 USDT
usdt_equiv_dict = {}
for _, row in df_equiv.iterrows():
    b = str(row.get('base', '')).strip()
    v = str(row.get('1_usdt_equivale_base', '')).strip()
    if not b or not v or v.lower() == 'nan':
        continue
    try:
        usdt_equiv_dict[b] = Decimal(v)
    except (InvalidOperation, ValueError):
        continue

filas = []
for _, row in df_base_solo.iterrows():
    base  = str(row.get('base', '')).strip()
    quote = str(row.get('quote', '')).strip()
    symbol = str(row.get('symbol', '')).strip()

    # Precio directo del par (1 BASE en QUOTE) si vino en el CSV
    p_base_en_quote = row.get('1_base_equivale_x_quote', '')
    if p_base_en_quote and p_base_en_quote.lower() != 'nan':
        try:
            p_base_en_quote = Decimal(str(p_base_en_quote))
        except (InvalidOperation, ValueError):
            p_base_en_quote = None
    else:
        p_base_en_quote = None

    try:
        if base in usdt_equiv_dict and p_base_en_quote is not None:
            # 1 USDT = X BASE; 1 BASE = Y QUOTE → 1 USDT = X*Y QUOTE
            usdt_to_base = usdt_equiv_dict[base]
            quote_rinde  = usdt_to_base * p_base_en_quote

            filas.append({
                'symbol': symbol,
                'base': base,
                'quote': quote,
                '1_dolar_equivale_a_quote': str(quote_rinde)
            })
        else:
            # Mensaje informativo si faltan insumos
            if base not in usdt_equiv_dict:
                print(f"⚠️ Sin equivalencia USDT→{base}")
            if p_base_en_quote is None:
                print(f"⚠️ Sin precio base→quote para {symbol}")
    except Exception as e:
        print(f"❌ Error procesando {symbol}: {e}")

# Guardar archivo final
os.makedirs(os.path.dirname(path_salida), exist_ok=True)
df_resultado = pd.DataFrame(filas)
df_resultado.to_csv(path_salida, index=False)

print("✅ Archivo generado (Binance) con equivalencias por base:")
print(f"📄 {path_salida}")
