# ruta: /codigo/binance/unificar_cotizaciones_usdt.py

import os
import sys
from pathlib import Path
import pandas as pd
from decimal import Decimal, getcontext

# Precisión quirúrgica para cálculos financieros
getcontext().prec = 50

# Directorios base (con subcarpeta por exchange)
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from codigo.config import EXCHANGE_ID  # usar config central
base_dir = os.path.dirname(__file__)

path_quote   = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', 'cotizaciones_indirectas_por_quote.csv')
path_base    = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', 'cotizaciones_indirectas_por_base.csv')
path_directo = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'cotizaciones_directas_usdt', '1_a_cotizaciones_usdt.csv')
path_salida  = os.path.join(base_dir, 'datos', EXCHANGE_ID, 'previo_a_cotizar', 'cotizaciones_usdt_unificadas.csv')

# Validaciones de existencia (avisa, pero sigue con lo que haya)
def _safe_read_csv(path):
    if not os.path.exists(path):
        print(f"⚠️ No se encontró: {path} (se omite)")
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str)

# Leer archivos de entrada como string para precisión
df_quote   = _safe_read_csv(path_quote)
df_base    = _safe_read_csv(path_base)
df_directo = _safe_read_csv(path_directo)

# Etiquetas de origen
if not df_quote.empty:
    df_quote['cotizacion'] = 'indirecto_por_quote'
if not df_base.empty:
    df_base['cotizacion'] = 'indirecto_por_base'
if not df_directo.empty:
    df_directo['cotizacion'] = 'directo'

# Solo columnas necesarias
cols_indirectos = ['symbol', 'base', 'quote', '1_dolar_equivale_a_quote', 'cotizacion']
if not df_quote.empty:
    df_quote = df_quote[cols_indirectos]
if not df_base.empty:
    df_base = df_base[cols_indirectos]

# Para los directos: asignar 1 fijo
if not df_directo.empty:
    df_directo = df_directo[['symbol', 'base', 'quote', 'cotizacion']]
    df_directo['1_dolar_equivale_a_quote'] = '1'
    df_directo = df_directo[cols_indirectos]

# Unificar todos (ignorando los que estén vacíos)
dfs = [d for d in [df_directo, df_quote, df_base] if not d.empty]
if not dfs:
    raise SystemExit("❌ No hay fuentes disponibles para unificar cotizaciones.")

df_total = pd.concat(dfs, ignore_index=True)

# Crear carpetas destino
os.makedirs(os.path.dirname(path_salida), exist_ok=True)

# Guardar archivo principal
df_total.to_csv(path_salida, index=False)

# Guardar copia para módulo de absorción (carpeta hermana de /codigo/)
# Copia para módulo de absorción dentro del mismo repo del motor
path_absorcion_dir = os.path.join(os.path.dirname(base_dir), 'modulo_absorcion')
os.makedirs(path_absorcion_dir, exist_ok=True)
archivo_absorcion = os.path.join(path_absorcion_dir, 'cotizaciones_equivalentes_1_usdt.csv')
df_total.to_csv(archivo_absorcion, index=False)

# Mensajes de éxito
print("✅ Archivo principal generado:")
print(f"📄 {path_salida}")
print("✅ Copia generada para módulo de absorción:")
print(f"📁 {archivo_absorcion}")
