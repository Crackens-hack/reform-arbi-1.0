import os
import pandas as pd
from decimal import Decimal, getcontext

# Configuración de precisión máxima para valores financieros
getcontext().prec = 50

# Rutas base
base_dir = os.path.dirname(__file__)
path_quote = os.path.join(base_dir, 'datos', 'previo_a_cotizar', 'cotizaciones_indirectas_por_quote.csv')
path_base = os.path.join(base_dir, 'datos', 'previo_a_cotizar', 'cotizaciones_indirectas_por_base.csv')
path_directo = os.path.join(base_dir, 'datos', 'cotizaciones_directas_usdt', '1_a_cotizaciones_usdt.csv')
path_salida = os.path.join(base_dir, 'datos', 'previo_a_cotizar', 'cotizaciones_usdt_unificadas.csv')

# Cargar archivos de entrada
df_quote = pd.read_csv(path_quote, dtype=str)
df_base = pd.read_csv(path_base, dtype=str)
df_directo = pd.read_csv(path_directo, dtype=str)

# Agregar columna de tipo de cotización
df_quote['cotizacion'] = 'indirecto_por_quote'
df_base['cotizacion'] = 'indirecto_por_base'
df_directo['cotizacion'] = 'directo'

# Unificar columna clave
df_directo.rename(columns={'1_usdt_equivale_base': '1_dolar_equivale_a_quote'}, inplace=True)

# Dejar solo columnas clave, en orden
df_quote = df_quote[['symbol', 'base', 'quote', '1_dolar_equivale_a_quote', 'cotizacion']]
df_base = df_base[['symbol', 'base', 'quote', '1_dolar_equivale_a_quote', 'cotizacion']]
df_directo = df_directo[['symbol', 'base', 'quote', '1_dolar_equivale_a_quote', 'cotizacion']]

# Unir todos los registros
df_total = pd.concat([df_directo, df_quote, df_base], ignore_index=True)

# Guardado principal
df_total.to_csv(path_salida, index=False)

# 🔁 Guardar copia para el módulo de absorción
path_absorcion = os.path.join(os.path.dirname(base_dir), 'modulo_absorcion')
os.makedirs(path_absorcion, exist_ok=True)
archivo_absorcion = os.path.join(path_absorcion, 'cotizaciones_equivalentes_1_usdt.csv')
df_total.to_csv(archivo_absorcion, index=False)

# Mensajes de éxito
print("✅ Archivo principal generado:")
print(f"📄 {path_salida}")
print("✅ Copia generada para módulo de absorción:")
print(f"📁 {archivo_absorcion}")
