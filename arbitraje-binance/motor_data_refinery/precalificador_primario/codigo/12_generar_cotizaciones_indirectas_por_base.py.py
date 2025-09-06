# ruta: /codigo/generar_cotizaciones_indirectas_por_base.py

import os
import pandas as pd
from decimal import Decimal, getcontext

# Precisión máxima para evitar errores de redondeo
getcontext().prec = 50

# Rutas
base_dir = os.path.dirname(__file__)
path_base_solo = os.path.join(base_dir, 'datos', 'previo_a_cotizar', '2_solo_base_calculable.csv')
path_usdt_equiv = os.path.join(base_dir, 'datos', 'cotizaciones_directas_usdt', '2_a_usdt_equivale_base.csv')
path_salida = os.path.join(base_dir, 'datos', 'previo_a_cotizar', 'cotizaciones_indirectas_por_base.csv')

# Cargar datos
df_base_solo = pd.read_csv(path_base_solo, dtype=str)
df_equiv = pd.read_csv(path_usdt_equiv, dtype=str)

# Diccionario: base → cuánto rinde 1 USDT en esa base
usdt_equiv_dict = {
    row['base']: str(row['1_usdt_equivale_base']) for _, row in df_equiv.iterrows()
}

# Lista para resultados
filas = []

for _, row in df_base_solo.iterrows():
    base = row['base']
    quote = row['quote']
    symbol = row['symbol']
    
    try:
        if base in usdt_equiv_dict and row['1_base_equivale_x_quote'] not in [None, '', 'nan']:
            usdt_to_base = Decimal(usdt_equiv_dict[base])
            base_to_quote = Decimal(str(row['1_base_equivale_x_quote']))
            quote_rinde = usdt_to_base * base_to_quote

            filas.append({
                'symbol': symbol,
                'base': base,
                'quote': quote,
                '1_dolar_equivale_a_quote': str(quote_rinde)
            })
        else:
            print(f"⚠️ Sin datos para base {base} o precio faltante para {symbol}")
    except Exception as e:
        print(f"❌ Error procesando {symbol}: {e}")

# Guardar archivo final
df_resultado = pd.DataFrame(filas)
df_resultado.to_csv(path_salida, index=False)

print("✅ Archivo generado con equivalencias por base:")
print(f"📄 {path_salida}")
