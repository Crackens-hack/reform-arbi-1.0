# codigo/7_generar_cotizaciones.py
"""
Genera cotizaciones directas contra la moneda de referencia (USDT, USDC, etc.)
usando la tabla indicada en static/config_cotizacion_directa.csv.

Objetivo: producir el mismo producto que el precalificador histórico, pero
parametrizado por exchange (config.EXCHANGE_ID) y directorios por exchange.

Salidas compatibles con el unificador y módulo de absorción:
- codigo/datos/<exchange>/cotizaciones_directas_usdt/1_a_cotizaciones_usdt.csv
    columnas: symbol, base, quote, 1_base_equivale_usdt, 1_usdt_equivale_base
"""

import pandas as pd
import ccxt
from decimal import Decimal, getcontext
from pathlib import Path
import sys

# --- Fix imports ---
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from codigo.config import DATOS_DIR, EXCHANGE_ID, CCXT_OPTIONS

CONFIG_FILE = ROOT_DIR / "codigo" / "static" / "config_cotizacion_directa.csv"

# Máxima precisión interna para cálculos
getcontext().prec = 50

def cargar_config():
    """Lee config_cotizacion_directa.csv → {tabla_origen, interesado_en}"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"❌ No se encontró {CONFIG_FILE}")
    df_cfg = pd.read_csv(CONFIG_FILE)
    if df_cfg.empty:
        raise ValueError(f"❌ {CONFIG_FILE} vacío")
    return {
        "tabla": df_cfg.loc[0, "tabla_origen"],
        "interesado_en": df_cfg.loc[0, "interesado_en"].upper().strip()
    }

def main():
    cfg = cargar_config()
    tabla_origen = cfg["tabla"]
    interesado_en = cfg["interesado_en"]

    # Ruta del CSV de entrada (generado por 6_symbolos_separacion.py)
    input_path = DATOS_DIR / "tratamiento_de_cotizacion" / f"{tabla_origen}.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"❌ No existe el archivo de entrada: {input_path}")

    df_in = pd.read_csv(input_path, dtype=str)
    if df_in.empty:
        raise RuntimeError(f"⚠️ {tabla_origen} está vacío.")

    # CCXT – exchange desde config
    ex_class = getattr(ccxt, EXCHANGE_ID)
    exchange = ex_class(CCXT_OPTIONS)
    exchange.load_markets()

    cotizaciones = []
    for _, row in df_in.iterrows():
        symbol = row["symbol"]
        try:
            ticker = exchange.fetch_ticker(symbol)
            last = ticker.get("last") or ticker.get("close") or ticker.get("info", {}).get("lastPrice")
            if not last:
                print(f"⚠️ Sin precio: {symbol}")
                continue
            precio = Decimal(str(last))
            base, quote = symbol.split("/")
            cotizaciones.append({
                "symbol": symbol,
                "base": base,
                "quote": quote,
                "1_base_equivale_usdt": precio,  # 1 base equivale a X USDT
                "1_usdt_equivale_base": (Decimal("1")/precio) if precio != 0 else None
            })
        except Exception as e:
            print(f"⚠️ Error {symbol}: {e}")

    if not cotizaciones:
        raise RuntimeError("❌ No se generaron cotizaciones.")

    # Salida por exchange para compatibilidad con unificador/absorción
    out_dir = DATOS_DIR / EXCHANGE_ID / "cotizaciones_directas_usdt"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = out_dir / "1_a_cotizaciones_usdt.csv"

    df = pd.DataFrame(cotizaciones)
    # 🔧 Limitar decimales de salida (mantén precisión alta)
    df["1_base_equivale_usdt"] = df["1_base_equivale_usdt"].apply(lambda x: f"{x:.10f}")
    df["1_usdt_equivale_base"] = df["1_usdt_equivale_base"].apply(lambda x: f"{x:.18f}" if x is not None else "")

    df.to_csv(output_csv, index=False)

    # CSV plano {base: 1_usdt_equivale_base} para pasos indirectos
    plano_csv = out_dir / "2_a_usdt_equivale_base.csv"
    df_plano = (
        df[["base", "1_usdt_equivale_base"]]
        .dropna(subset=["1_usdt_equivale_base"])
    )
    df_plano.to_csv(plano_csv, index=False)

    print(f"✅ Cotizaciones directas generadas en: {output_csv} ({len(df)} filas)")
    print(f"✅ Equivalencias planas generadas en: {plano_csv}")

if __name__ == "__main__":
    main()
