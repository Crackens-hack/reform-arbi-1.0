"""
Genera una exportación de símbolos con campos ESTANDARIZADOS independiente del exchange.

Lee markets desde CCXT, aplana las estructuras y aplica el mapeo definido en
`codigo/static/campos_estandar.py` para producir un CSV en `codigo/datos/estandar/`.

Dominus puede ajustar los mapeos en tiempo real modificando `campos_estandar.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
from decimal import Decimal

import pandas as pd
import ccxt

# Rutas/imports robustos
THIS_DIR = Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

from codigo.config import EXCHANGE_ID, CCXT_OPTIONS, DATOS_DIR  # type: ignore
from codigo.static.campos_estandar import TARGET_FIELDS, MAPPING  # type: ignore


def flatten_json(value: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(value, dict):
        for k, v in value.items():
            out.update(flatten_json(v, f"{prefix}{k}_"))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            if isinstance(item, (dict, list)):
                out.update(flatten_json(item, f"{prefix}{idx}_"))
            else:
                out[f"{prefix}{idx}"] = item
    else:
        out[prefix[:-1]] = value
    return out


def main() -> None:
    exchange_id = EXCHANGE_ID
    mapping = MAPPING.get(exchange_id, {})
    if not mapping:
        raise RuntimeError(
            f"❌ No hay mapeo definido para '{exchange_id}' en codigo/static/campos_estandar.py"
        )

    # Instanciar exchange y cargar markets
    ex_class = getattr(ccxt, exchange_id)
    ex = ex_class(CCXT_OPTIONS)
    ex.load_markets()

    rows_out = []
    for symbol, market in ex.markets.items():
        flat = flatten_json(market)
        normalized: Dict[str, Any] = {k: None for k in TARGET_FIELDS}

        # Asignación por mapeo (source_key -> target_field)
        for source_key, target_field in mapping.items():
            val = flat.get(source_key)
            # Normalizaciones simples
            if isinstance(val, bool):
                normalized[target_field] = val
            elif isinstance(val, (int, float, Decimal)):
                normalized[target_field] = str(val)
            elif val is None:
                normalized[target_field] = None
            else:
                normalized[target_field] = str(val)

        # Asegurar clave de identificación
        normalized["symbol"] = normalized.get("symbol") or symbol
        normalized["base"] = normalized.get("base") or market.get("base")
        normalized["quote"] = normalized.get("quote") or market.get("quote")

        rows_out.append(normalized)

    # Exportar CSV
    out_dir = DATOS_DIR / "estandar"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"symbols_estandar_{exchange_id}.csv"

    df = pd.DataFrame(rows_out)
    df.to_csv(out_csv, index=False)
    print(f"✅ Export estandarizada generada: {out_csv} ({len(df)} símbolos)")


if __name__ == "__main__":
    main()

