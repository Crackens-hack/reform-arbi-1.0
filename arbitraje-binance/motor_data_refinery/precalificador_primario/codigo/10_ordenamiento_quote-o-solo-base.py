# ruta: /codigo/script_filtrado_pares.py

import pandas as pd
import os
from decimal import Decimal

# Ruta base del directorio donde se encuentran los datos (asume que el script se ejecuta desde /codigo/)
ruta_datos = os.path.join(os.path.dirname(__file__), 'datos', 'previo_a_cotizar')

# Ruta completa al archivo CSV de entrada con los pares ya filtrados previamente
ruta_entrada = os.path.join(ruta_datos, 'pares_indirectos_filtrados.csv')

# Cargar el archivo CSV sin convertir automáticamente a tipos numéricos para evitar pérdida de precisión
# Todos los datos se cargan como strings
df = pd.read_csv(ruta_entrada, dtype=str)

# Para cada una de estas columnas (si existen), convertir sus valores a tipo Decimal con alta precisión
for col in ['1_base_equivale_x_quote', '1_quote_equivale_x_base']:
    if col in df.columns:
        # Solo convertir valores válidos; si hay nulos o strings vacíos se dejan como ''
        df[col] = df[col].apply(lambda x: str(Decimal(x)) if x not in [None, '', 'nan'] else '')

# --- FUNCIONES AUXILIARES PARA CLASIFICAR ---

# Esta función retorna True si el valor es calculable desde el quote (no es "quote:NONE")
def es_quote_calculable(valor):
    return 'quote:NONE' not in valor

# Esta función retorna True solo si hay base calculable pero no hay quote (es solo "base")
def es_solo_base_calculable(valor):
    return 'quote:NONE' in valor and 'base:NONE' not in valor

# --- FILTRADO SEGÚN CRITERIOS LÓGICOS ---

# Filtro los pares donde hay posibilidad de cálculo por el quote, o donde hay ambos (base y quote)
df_quote_calculable_o_mixto = df[df['cotiza_vs_directo'].apply(es_quote_calculable)]

# Filtro los pares donde solo la base es calculable (el quote está como NONE)
df_base_solo = df[df['cotiza_vs_directo'].apply(es_solo_base_calculable)]

# --- GUARDADO DE ARCHIVOS DE SALIDA ---

# Guardar los resultados en CSV sin truncamiento decimal, en el mismo directorio de entrada
df_quote_calculable_o_mixto.to_csv(os.path.join(ruta_datos, '1_quote_calculable_o_mixto.csv'), index=False)
df_base_solo.to_csv(os.path.join(ruta_datos, '2_solo_base_calculable.csv'), index=False)

# Mensaje final informando éxito y nombres de archivos generados
print("✅ Archivos generados con máxima precisión en 'codigo/datos/previo_a_cotizar':")
print("📄 1_quote_calculable_o_mixto.csv")
print("📄 2_solo_base_calculable.csv")
