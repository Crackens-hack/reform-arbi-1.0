# app/codigo/3_validar_estructura.py
"""
Valida que los datos estructurales cargados estén consistentes y completos
comparando la base de datos (tablas 'sym_*') contra los datos reales de CCXT
(`load_markets()`), usando el MISMO aplanado que usamos al cargar.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ── Imports del paquete de config (robustos para ambos modos de ejecución)
THIS_DIR = Path(__file__).resolve().parent
try:
    # python -m codigo.3_validar_estructura
    from .config import (
        EXCHANGE_ID, CCXT_OPTIONS,
        connect,
    )
except Exception:
    # python codigo/3_validar_estructura.py
    sys.path.insert(0, str(THIS_DIR))
    from config import (  # type: ignore
        EXCHANGE_ID, CCXT_OPTIONS,
        connect,
    )

import pymysql
import pandas as pd
import numpy as np
import ccxt

TOLERANCIA = 1e-8  # tolerancia numérica para floats


# ───────────────────────── Helpers ─────────────────────────

def flatten_json(value: Any, prefix: str = "") -> Dict[str, Any]:
    """
    MISMO aplanado que usa el cargador:
      - dict → prefijo 'key_'
      - list → indices 'key_0', 'key_1', ...
      - escalares → clave completa sin '_' final
    Ejemplos de salida: 'precision_amount', 'limits_price_min', 'info_status'
    """
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


def get_sym_tables(conn: pymysql.connections.Connection) -> List[str]:
    """Retorna todas las tablas que comienzan con 'sym_' en el schema actual."""
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        rows = cursor.fetchall()
        # formato dict o tuple según cursorclass; convertimos a texto:
        names: List[str] = []
        for r in rows:
            if isinstance(r, dict):
                # primer valor del dict (Tables_in_xxx)
                names.append(next(iter(r.values())))
            else:
                names.append(r[0])
        return [t for t in names if t.startswith("sym_")]


def read_tables_grouped_by_symbol(conn: pymysql.connections.Connection, tables: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Lee todas las tablas sym_* y agrupa sus columnas por symbol_id.
    Si hay colisiones de nombres, la última tabla leída pisa (no debería ocurrir si schema es disjunto).
    """
    per_symbol: Dict[str, Dict[str, Any]] = {}
    for tbl in tables:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{tbl}`")
            rows = cursor.fetchall()
            for row in rows:
                sym_id = row.get("symbol_id") if isinstance(row, dict) else None
                if not sym_id:
                    continue
                if sym_id not in per_symbol:
                    per_symbol[sym_id] = {}
                # merge excepto symbol_id
                for k, v in row.items():
                    if k == "symbol_id":
                        continue
                    per_symbol[sym_id][k] = v
    return per_symbol


def almost_equal(a: Any, b: Any, tol: float = TOLERANCIA) -> bool:
    """Comparación laxa para floats; exacta para strings/otros."""
    # Trata de comparar como float si ambos son parseables
    try:
        fa = float(a)
        fb = float(b)
        if np.isnan(fa) and np.isnan(fb):
            return True
        return abs(fa - fb) <= tol
    except Exception:
        # Comparación exacta como string
        return str(a) == str(b)


def compare_symbol(
    sym_id: str,
    db_dict: Dict[str, Any],
    ccxt_market: Dict[str, Any],
) -> List[str]:
    """
    Compara todas las claves presentes en db_dict contra el market aplanado de CCXT.
    Devuelve lista de errores (strings) o lista vacía si todo OK.
    """
    flat_ccxt = flatten_json(ccxt_market)  # aplanado completo con prefijos
    errs: List[str] = []

    # Recuperamos el symbol para mensajes
    symbol = db_dict.get("symbol") or flat_ccxt.get("symbol") or "<?>"

    for k_db, v_db in db_dict.items():
        if k_db in {"exchange", "symbol", "symbol_id"}:
            continue
        # Ojo: algunas columnas pueden venir como None/NULL por normalización
        v_ccxt = flat_ccxt.get(k_db, None)
        if v_ccxt is None and v_db is None:
            continue
        if v_ccxt is None and v_db is not None:
            errs.append(f"{sym_id} ({symbol}) → ⚠️ campo '{k_db}' no existe en CCXT (DB={v_db})")
            continue
        if not almost_equal(v_db, v_ccxt):
            errs.append(f"{sym_id} ({symbol}) → ❌ '{k_db}': DB={v_db} vs CCXT={v_ccxt}")
    return errs


# ───────────────────────── Main ─────────────────────────

def main() -> None:
    # 1) CCXT
    try:
        ex = getattr(ccxt, EXCHANGE_ID)(CCXT_OPTIONS)
        ex.load_markets()
    except Exception as e:
        print(f"❌ No se pudo instanciar CCXT para '{EXCHANGE_ID}': {e}")
        return

    # 2) DB + tablas sym_*
    conn = connect()
    try:
        tables = get_sym_tables(conn)
        if not tables:
            print("❌ No se encontraron tablas 'sym_*' en la base.")
            return

        per_symbol = read_tables_grouped_by_symbol(conn, tables)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    total = len(per_symbol)
    print(f"🔎 Validando {total} símbolos en '{EXCHANGE_ID}' contra CCXT…")
    errors: List[str] = []

    # 3) Comparación por símbolo
    for i, (sym_id, db_dict) in enumerate(per_symbol.items(), 1):
        symbol = db_dict.get("symbol")
        if not symbol:
            errors.append(f"{sym_id} → ⚠️ no tiene 'symbol' en DB")
            continue
        market = ex.markets.get(symbol)
        if not market:
            errors.append(f"{sym_id} → ❌ símbolo '{symbol}' no existe en CCXT")
            continue

        errors.extend(compare_symbol(sym_id, db_dict, market))

        if i % 250 == 0:
            print(f"→ Validados {i}/{total}…")

    # 4) Resultado
    if errors:
        print("\n❌ Inconsistencias encontradas:")
        for e in errors:
            print("-", e)
    else:
        print(f"\n✔️ Todos los {total} símbolos coinciden con CCXT.")

    print("\n🎯 Validación completa.")


if __name__ == "__main__":
    main()
