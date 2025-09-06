# codigo/6_symbolos_separacion.py
"""
Separa símbolos de la tabla funcional en:
- cotizador_directo   (quote == USDT)
- cotizador_invertido (base  == USDT)
- cotizador_indirecto (ninguno == USDT)

Entrada:
    - Usa config_separador.csv para saber tabla origen e interesado_en
Salida:
    - CSVs en codigo/datos/tratamiento_de_cotizacion/
"""

import sys, os
from pathlib import Path
import pandas as pd
import pymysql

# --- Fix de imports: asegurar que /app esté en sys.path ---
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from codigo.config import connect, DATOS_DIR

# --- Configuración ---
CONFIG_FILE = Path(__file__).resolve().parent / "static" / "config_separador.csv"

def cargar_config():
    """Lee config_separador.csv -> dict con {tabla_a_separar, interesado_en}"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"❌ No se encontró {CONFIG_FILE}")
    df_cfg = pd.read_csv(CONFIG_FILE)
    if df_cfg.empty:
        raise ValueError(f"❌ {CONFIG_FILE} vacío")
    return {
        "tabla": df_cfg.loc[0, "tabla_a_separar"],
        "interesado_en": df_cfg.loc[0, "interesado_en"].upper().strip()
    }

def main():
    cfg = cargar_config()
    tabla_origen = cfg["tabla"]
    interesado_en = cfg["interesado_en"]

    # Conexión DB
    conn = connect()
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", (tabla_origen,))
        if cursor.fetchone() is None:
            raise RuntimeError(f"❌ La tabla origen `{tabla_origen}` no existe en la DB.")
        cursor.execute(f"SELECT symbol, base, quote FROM `{tabla_origen}`")
        rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"⚠️ La tabla `{tabla_origen}` no tiene datos.")

    # Normalizar
    for col in ("symbol", "base", "quote"):
        df[col] = df[col].astype(str).str.strip().str.upper()

    # Separar
    directo   = df[df["quote"] == interesado_en]
    invertido = df[df["base"]  == interesado_en]
    indirecto = df[(df["base"] != interesado_en) & (df["quote"] != interesado_en)]

    # --- Exportar ---
    output_dir = DATOS_DIR / "tratamiento_de_cotizacion"
    output_dir.mkdir(parents=True, exist_ok=True)

    directo.to_csv(  output_dir / f"cotizador_directo_{interesado_en}.csv",   index=False)
    invertido.to_csv(output_dir / f"cotizador_invertido_{interesado_en}.csv", index=False)
    indirecto.to_csv(output_dir / f"cotizador_indirecto_{interesado_en}.csv", index=False)

    print(f"✅ Exportados en {output_dir}")
    print(f"✔ cotizador_directo_{interesado_en}.csv:   {len(directo)} símbolos")
    print(f"✔ cotizador_invertido_{interesado_en}.csv: {len(invertido)} símbolos")
    print(f"✔ cotizador_indirecto_{interesado_en}.csv: {len(indirecto)} símbolos")

if __name__ == "__main__":
    main()
