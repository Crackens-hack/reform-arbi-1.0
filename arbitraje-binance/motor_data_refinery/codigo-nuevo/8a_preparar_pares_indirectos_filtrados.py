"""
Prepara `pares_indirectos_filtrados.csv` sin DB, usando CCXT + salidas de directos.

Entradas:
- codigo/datos/<exchange>/cotizaciones_directas_usdt/2_a_usdt_equivale_base.csv
  (mapea token base → 1_usdt_equivale_base)
- CCXT markets/tickers para obtener precio 1_base_equivale_x_quote

Salida:
- codigo/datos/<exchange>/previo_a_cotizar/pares_indirectos_filtrados.csv
  columnas: symbol, base, quote, 1_base_equivale_x_quote, cotiza_vs_directo

Regla para `cotiza_vs_directo`:
- Si quote ∈ dict_equiv_usdt → marca como calculable desde quote (no incluye 'quote:NONE').
- Si NO y base ∈ dict_equiv_usdt → marca como solo_base_calculable ('quote:NONE').
"""

from __future__ import annotations

from pathlib import Path
import sys
from decimal import Decimal
import pandas as pd
import ccxt

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from codigo.config import DATOS_DIR, EXCHANGE_ID, CCXT_OPTIONS  # type: ignore


def main() -> None:
    ex_class = getattr(ccxt, EXCHANGE_ID)
    ex = ex_class(CCXT_OPTIONS)
    ex.load_markets()

    # Cargar dict USDT → BASE unidades
    direct_dir = DATOS_DIR / EXCHANGE_ID / "cotizaciones_directas_usdt"
    direct_csv = direct_dir / "2_a_usdt_equivale_base.csv"
    if not direct_csv.exists():
        raise FileNotFoundError(f"❌ Falta {direct_csv}. Ejecuta 7_generar_cotizaciones_directas primero.")
    df_equiv = pd.read_csv(direct_csv, dtype=str)
    equiv = {str(r["base"]).strip().upper(): str(r["1_usdt_equivale_base"]).strip() for _, r in df_equiv.iterrows() if str(r.get("1_usdt_equivale_base", "")).strip()}

    rows = []
    for symbol, m in ex.markets.items():
        base = (m.get("base") or "").upper()
        quote = (m.get("quote") or "").upper()
        if not base or not quote:
            continue
        if base == "USDT" or quote == "USDT":
            continue  # indirectos = pares que no involucran USDT directo

        # Precio 1 base en quote
        price = None
        try:
            t = ex.fetch_ticker(symbol)
            last = t.get("last") or t.get("close") or (t.get("info", {}) or {}).get("lastPrice")
            if last is not None:
                price = str(Decimal(str(last)))
        except Exception:
            price = None

        # Clasificación de calculabilidad contra el directo
        quote_ok = quote in equiv
        base_ok = base in equiv
        if quote_ok:
            flag = "base:OK|quote:OK" if base_ok else "base:NONE|quote:OK"
        elif base_ok:
            flag = "base:OK|quote:NONE"
        else:
            # sin camino directo por base ni por quote: igual lo dejamos fuera para los siguientes pasos
            flag = "base:NONE|quote:NONE"

        rows.append({
            "symbol": symbol,
            "base": base,
            "quote": quote,
            "1_base_equivale_x_quote": price or "",
            "1_quote_equivale_x_base": (str(Decimal("1")/Decimal(price)) if price and Decimal(price) != 0 else ""),
            "cotiza_vs_directo": flag,
        })

    out_dir = DATOS_DIR / EXCHANGE_ID / "previo_a_cotizar"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "pares_indirectos_filtrados.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"✅ Generado {out_csv} ({len(rows)} pares)")


if __name__ == "__main__":
    main()

