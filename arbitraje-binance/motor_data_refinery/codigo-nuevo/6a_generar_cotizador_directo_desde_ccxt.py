"""
Genera `codigo/datos/tratamiento_de_cotizacion/cotizador_directo_<QUOTE>.csv`
directamente desde CCXT (sin DB), para alimentar 7_generar_cotizaciones_directas.

Lee `static/config_cotizacion_directa.csv` para conocer el QUOTE objetivo.
"""

from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd
import ccxt

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from codigo.config import DATOS_DIR, EXCHANGE_ID, CCXT_OPTIONS  # type: ignore

CONFIG_FILE = ROOT_DIR / "codigo" / "static" / "config_cotizacion_directa.csv"


def cargar_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"❌ No se encontró {CONFIG_FILE}")
    df_cfg = pd.read_csv(CONFIG_FILE)
    if df_cfg.empty:
        raise ValueError(f"❌ {CONFIG_FILE} vacío")
    return {
        "tabla": df_cfg.loc[0, "tabla_origen"],
        "interesado_en": df_cfg.loc[0, "interesado_en"].upper().strip(),
    }


def main() -> None:
    cfg = cargar_config()
    quote_target = cfg["interesado_en"]

    # Cargar symbols desde el exchange configurado
    ex_class = getattr(ccxt, EXCHANGE_ID)
    ex = ex_class(CCXT_OPTIONS)
    ex.load_markets()

    rows = []
    for symbol, m in ex.markets.items():
        base = m.get("base")
        quote = m.get("quote")
        if not base or not quote:
            continue
        if quote.upper() == quote_target:
            rows.append({"symbol": symbol, "base": base, "quote": quote})

    if not rows:
        raise SystemExit(f"❌ No se encontraron pares con quote={quote_target} en {EXCHANGE_ID}")

    out_dir = DATOS_DIR / "tratamiento_de_cotizacion"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"cotizador_directo_{quote_target}.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"✅ Generado {out_csv} ({len(rows)} símbolos)")


if __name__ == "__main__":
    main()

