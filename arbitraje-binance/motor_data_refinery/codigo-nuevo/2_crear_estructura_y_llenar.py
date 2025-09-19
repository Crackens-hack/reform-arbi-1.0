# app/codigo/2_crear_estructura_y_llenar.py
from __future__ import annotations

import os, sys, json, re
from typing import Any, Dict, List, Set
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
try:
    # Ejecución como módulo: python -m codigo.2_crear_estructura_y_llenar
    from .config import (
        EXCHANGE_ID, CCXT_OPTIONS,
        ensure_runtime_dirs, load_schema_or_abort,
        AUDIT_STRUCT_EXPORT, ESTRUCTURAL_DIR,
        connect,
    )
except Exception:
    # Ejecución directa: python codigo/2_crear_estructura_y_llenar.py
    # Agregamos .../codigo al sys.path para importar el paquete 'config'
    sys.path.insert(0, str(THIS_DIR))
    from config import (  # type: ignore
        EXCHANGE_ID, CCXT_OPTIONS,
        ensure_runtime_dirs, load_schema_or_abort,
        AUDIT_STRUCT_EXPORT, ESTRUCTURAL_DIR,
        connect,
    )

import ccxt
import numpy as np
import pandas as pd
import pymysql


# ────────────────────────── Helpers ──────────────────────────
def sanitize_name(name: str) -> str:
    """SQL-safe para nombres de columnas (sin backticks)."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def flatten_json(value: Any, prefix: str = "") -> Dict[str, Any]:
    """
    Aplana dict/list a clave=valor (una capa).
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


def flatten_schema_keys(node: Any, prefix: str = "") -> Set[str]:
    """
    A partir de un sub-schema dict, genera el set de claves aplanadas esperadas.
    Ej: {"precision": {"amount": "float"}} con prefix='precision_' → {'precision_amount'}
    """
    keys: Set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, dict):
                keys |= flatten_schema_keys(v, prefix + k + "_")
            else:
                keys.add((prefix + k).rstrip("_"))
    # Si es list/u otro tipo, no agregamos restricciones
    return keys


def pairs_to_single_row_map(arr: List[List[Any]], prefix: str) -> Dict[str, Any]:
    """
    Convierte [[x,y],[a,b],...] a un solo dict:
      { f"{prefix}_0_x": x, f"{prefix}_0_y": y, f"{prefix}_1_x": a, f"{prefix}_1_y": b, ... }
    """
    out: Dict[str, Any] = {}
    for i, item in enumerate(arr):
        if isinstance(item, list) and len(item) == 2:
            out[f"{prefix}_{i}_x"] = json.dumps(item[0])
            out[f"{prefix}_{i}_y"] = json.dumps(item[1])
    return out


def process_field(
    value: Any,
    key: str,
    base: Dict[str, Any],
    rows_dict: Dict[str, List[Dict[str, Any]]],
    schema_local: Dict[str, Any],
) -> None:
    """Procesa un campo anidado según el schema manual."""
    table_name = f"sym_{key}"

    if isinstance(value, dict):
        # 🔧 FIX: aplanar con prefijo 'key_' para alinear con flatten_schema_keys()
        flat_val = flatten_json(value, prefix=f"{key}_")
        schema_sub = schema_local.get(key)
        if isinstance(schema_sub, dict):
            allowed = flatten_schema_keys(schema_sub, prefix=f"{key}_")
            flat_val = {k: v for k, v in flat_val.items() if (k in allowed)}
        flat_val.update(base)
        rows_dict[table_name].append(flat_val)

    elif isinstance(value, list):
        if all(isinstance(i, list) and len(i) == 2 for i in value):
            # Guardamos TODO en UNA fila por símbolo (evita PK duplicada)
            safe_map = pairs_to_single_row_map(value, key)
            rows_dict[table_name].append({**base, **safe_map})
        else:
            safe_array = {f"{key}_{i}": json.dumps(v) for i, v in enumerate(value)}
            rows_dict[table_name].append({**base, **safe_array})


def build_relational_rows(
    exchange: ccxt.Exchange,
    symbols: List[str],
    schema_local: Dict[str, Any],
    exchange_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """Genera dict de listas por tabla `sym_<clave>` para campos anidados."""
    rows_rel: Dict[str, List[Dict[str, Any]]] = {
        f"sym_{k}": []
        for k, v in schema_local.items()
        if isinstance(v, (dict, list))
    }

    print(f"🔁 Procesando {len(symbols)} símbolos de {exchange_id}…")

    for symbol in symbols:
        try:
            market = exchange.markets[symbol]
            base_ref = {
                "exchange": exchange_id,                 # exchange como columna
                "symbol_id": f"{exchange_id}:{symbol}",  # trazabilidad
                "symbol": symbol,
            }
            for key in schema_local:
                if key in {"symbol_id", "symbol"}:
                    continue
                if isinstance(schema_local[key], (dict, list)):
                    process_field(market.get(key), key, base_ref, rows_rel, schema_local)
        except Exception as exc:
            print(f"⚠️ Error con símbolo {symbol}: {exc}")

    return rows_rel


def create_and_fill_tables(
    connection: pymysql.connections.Connection,
    rows_dict: Dict[str, List[Dict[str, Any]]],
) -> None:
    """Crea tablas neutrales `sym_*` y hace REPLACE INTO. Exporta CSV si está activado."""
    for table, rows in rows_dict.items():
        if not rows:
            continue

        df = pd.DataFrame(rows)
        df = df.where(pd.notnull(df), None).replace({np.nan: None})
        df.columns = [sanitize_name(col) for col in df.columns]

        # Tipos
        cols_sql_parts = [
            f"`{col}` VARCHAR(255)" if col in {"exchange", "symbol_id", "symbol"} else f"`{col}` TEXT"
            for col in df.columns
        ]
        # PK homogénea en symbol_id
        if "symbol_id" in df.columns:
            cols_sql_parts.append("PRIMARY KEY (`symbol_id`)")

        create_sql = "CREATE TABLE IF NOT EXISTS `{}` (\n    {}\n) CHARACTER SET utf8mb4;".format(
            table, ",\n    ".join(cols_sql_parts)
        )
        insert_sql = (
            f"REPLACE INTO `{table}` (" + ", ".join(f"`{c}`" for c in df.columns) + ") "
            f"VALUES ({', '.join(['%s'] * len(df.columns))});"
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(create_sql)
                cursor.executemany(insert_sql, df.values.tolist())
            connection.commit()
            print(f"✅ Tabla `{table}` creada/actualizada ({len(df)} filas).")
        except Exception as exc:
            print(f"⚠️ Error en tabla {table}: {exc}")

        # Auditoría opcional
        if AUDIT_STRUCT_EXPORT:
            ESTRUCTURAL_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(ESTRUCTURAL_DIR / f"{table}.csv", index=False)


def create_flat_symbols_table(
    connection: pymysql.connections.Connection,
    exchange_id: str,
    exchange: ccxt.Exchange,
    schema_local: Dict[str, Any],
    symbols: List[str],
) -> None:
    """Crea `sym_symbols` con una fila por símbolo; solo campos simples del schema."""
    table_name = "sym_symbols"
    rows: List[Dict[str, Any]] = []

    for symbol in symbols:
        try:
            market = exchange.markets[symbol]
            row = {"exchange": exchange_id, "symbol_id": f"{exchange_id}:{symbol}", "symbol": symbol}
            for key, value in market.items():
                if key in schema_local and not isinstance(schema_local[key], (dict, list)):
                    row[key] = value
            rows.append(row)
        except Exception as exc:
            print(f"⚠️ Error procesando {symbol} en tabla plana: {exc}")

    if not rows:
        print(f"⚠️ No se generaron datos para {table_name}")
        return

    df = pd.DataFrame(rows)
    df = df.where(pd.notnull(df), None).replace({np.nan: None})
    df.columns = [sanitize_name(col) for col in df.columns]

    cols_sql_parts = [
        f"`{col}` VARCHAR(255)" if col in {"exchange", "symbol_id", "symbol", "base", "quote"} else f"`{col}` TEXT"
        for col in df.columns
    ]
    if "symbol_id" in df.columns:
        cols_sql_parts.append("PRIMARY KEY (`symbol_id`)")

    create_sql = (
        f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n    "
        + ",\n    ".join(cols_sql_parts)
        + "\n) CHARACTER SET utf8mb4;"
    )
    insert_sql = (
        f"REPLACE INTO `{table_name}` (" + ", ".join(f"`{col}`" for col in df.columns) + ") "
        f"VALUES ({', '.join(['%s'] * len(df.columns))});"
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(create_sql)
            cursor.executemany(insert_sql, df.values.tolist())
        connection.commit()
        print(f"✅ Tabla `{table_name}` creada/actualizada ({len(df)} filas).")
    except Exception as exc:
        print(f"⚠️ Error creando o insertando en {table_name}: {exc}")

    # Auditoría opcional
    if AUDIT_STRUCT_EXPORT:
        ESTRUCTURAL_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(ESTRUCTURAL_DIR / f"{table_name}.csv", index=False)


# ────────────────────────── Orquestador ──────────────────────────
def main() -> None:
    # Asegurar carpetas runtime (importables y de auditoría)
    ensure_runtime_dirs()

    # 1) Cargar schema manual (obligatorio; sin fallback)
    schema_local: Dict[str, Any] = load_schema_or_abort()

    # 2) Instanciar exchange (CCXT)
    try:
        exchange = getattr(ccxt, EXCHANGE_ID)(CCXT_OPTIONS)
        exchange.load_markets()
    except Exception as exc:
        raise RuntimeError(f"❌ Error al cargar exchange {EXCHANGE_ID}: {exc}") from exc

    # 3) Símbolos spot/estándar (ignoramos sintéticos)
    symbols: List[str] = [s for s in exchange.symbols if "/" in s]

    # 4) Conexión DB
    connection = connect()

    try:
        rows_relacionales = build_relational_rows(exchange, symbols, schema_local, EXCHANGE_ID)
        create_and_fill_tables(connection, rows_relacionales)
        create_flat_symbols_table(connection, EXCHANGE_ID, exchange, schema_local, symbols)
    finally:
        try:
            connection.close()
        except Exception:
            pass

    print("🎯 Finalizado.")


if __name__ == "__main__":
    main()
