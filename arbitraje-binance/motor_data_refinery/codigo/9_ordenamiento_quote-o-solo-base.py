# ruta: /codigo/script_filtrado_pares_binance.py

import pandas as pd
import os
from decimal import Decimal, InvalidOperation

EXCHANGE_ID = "binance"

# Ruta base (asumiendo ejecución desde /codigo/)
BASE_DIR = os.path.dirname(__file__)
ruta_datos = os.path.join(BASE_DIR, 'datos', EXCHANGE_ID, 'previo_a_cotizar')

# Archivo de entrada (generado por el script de pares indirectos para Binance)
ruta_entrada = os.path.join(ruta_datos, 'pares_indirectos_filtrados.csv')

if not os.path.exists(ruta_entrada):
    raise FileNotFoundError(f"❌ No se encontró el CSV de entrada: {ruta_entrada}")

# Cargar todo como string para no perder precisión
df = pd.read_csv(ruta_entrada, dtype=str)

# Asegurar que exista la columna clave
if 'cotiza_vs_directo' not in df.columns:
    raise RuntimeError("❌ Falta la columna 'cotiza_vs_directo' en el CSV de entrada.")

# Convertir a string “plano” (conservando precisión) solo los valores válidos
for col in ['1_base_equivale_x_quote', '1_quote_equivale_x_base']:
    if col in df.columns:
        def _safe_decimal_str(x):
            if x in [None, '', 'nan', 'NaN']:
                return ''
            try:
                return str(Decimal(str(x)))
            except (InvalidOperation, ValueError):
                return ''
        df[col] = df[col].apply(_safe_decimal_str)

# --- FUNCIONES AUXILIARES ---

def es_quote_calculable(valor: str) -> bool:
    """True si el valor es calculable desde el quote (no contiene 'quote:NONE')."""
    return isinstance(valor, str) and ('quote:NONE' not in valor)

def es_solo_base_calculable(valor: str) -> bool:
    """True si solo base es calculable (tiene 'quote:NONE' y NO tiene 'base:NONE')."""
    return isinstance(valor, str) and ('quote:NONE' in valor and 'base:NONE' not in valor)

# --- FILTROS ---

df_quote_calculable_o_mixto = df[df['cotiza_vs_directo'].apply(es_quote_calculable)].copy()
df_base_solo = df[df['cotiza_vs_directo'].apply(es_solo_base_calculable)].copy()

# --- SALIDA ---

os.makedirs(ruta_datos, exist_ok=True)

out1 = os.path.join(ruta_datos, '1_quote_calculable_o_mixto.csv')
out2 = os.path.join(ruta_datos, '2_solo_base_calculable.csv')

df_quote_calculable_o_mixto.to_csv(out1, index=False)
df_base_solo.to_csv(out2, index=False)

print(f"✅ Archivos generados en '{ruta_datos}':")
print("📄 1_quote_calculable_o_mixto.csv")
print("📄 2_solo_base_calculable.csv")
