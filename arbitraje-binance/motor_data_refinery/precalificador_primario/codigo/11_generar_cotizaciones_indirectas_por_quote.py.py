# ruta: /codigo/generar_cotizaciones_indirectas_por_quote.py

import os
import pandas as pd
from decimal import Decimal, getcontext

# Precisión máxima para cálculos financieros
getcontext().prec = 50

# Rutas de entrada y salida
base_dir = os.path.dirname(__file__)
path_pares = os.path.join(base_dir, 'datos', 'previo_a_cotizar', '1_quote_calculable_o_mixto.csv')
path_equiv = os.path.join(base_dir, 'datos', 'cotizaciones_directas_usdt', '2_a_usdt_equivale_base.csv')
path_salida = os.path.join(base_dir, 'datos', 'previo_a_cotizar', 'cotizaciones_indirectas_por_quote.csv')

# Cargar archivos de entrada
df_pares = pd.read_csv(path_pares, dtype=str)
df_equiv = pd.read_csv(path_equiv, dtype=str)

# Crear diccionario: quote → cuánto rinde 1 USDT
usdt_equiv_dict = {
    row['base']: str(row['1_usdt_equivale_base']) for _, row in df_equiv.iterrows()
}

# Procesar cada fila
filas = []
for _, row in df_pares.iterrows():
    symbol = row['symbol']
    base = row['base']
    quote = row['quote']
    
    if quote in usdt_equiv_dict:
        filas.append({
            'symbol': symbol,
            'base': base,
            'quote': quote,
            '1_dolar_equivale_a_quote': usdt_equiv_dict[quote]
        })
    else:
        print(f"⚠️ Quote sin equivalencia directa en USDT: {quote}")

# Guardar archivo final
df_final = pd.DataFrame(filas)
df_final.to_csv(path_salida, index=False)

print("✅ Archivo generado:")
print(f"📄 {path_salida}")
