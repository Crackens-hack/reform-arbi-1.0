from __future__ import annotations  # Compatibilidad para anotaciones futuras en Python <3.10

# ---------------------------------------------------------------------------
# 📉 Fijar el path base para permitir importar correctamente schemas
# ---------------------------------------------------------------------------
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ruta absoluta al directorio /codigo
sys.path.insert(0, BASE_DIR)  # Se agrega como primer path de búsqueda

# ---------------------------------------------------------------------------
# 🧰 Librerías necesarias
# ---------------------------------------------------------------------------
import importlib
import json
import re
from typing import Any, Dict, List

import ccxt
import numpy as np
import pandas as pd
import pymysql
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Cargar credenciales y configuración de base de datos desde .env
# ---------------------------------------------------------------------------
load_dotenv()

DB_CONFIG: Dict[str, str] = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", ""),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# ---------------------------------------------------------------------------
# 2. Funciones auxiliares reutilizables
# ---------------------------------------------------------------------------

def sanitize_name(name: str) -> str:
    """Sanitiza nombres de columnas/tablas para SQL reemplazando caracteres inválidos."""
    return f"`{re.sub(r'[^a-zA-Z0-9_]', '_', name)}`"

def flatten_json(value: Any, prefix: str = "") -> Dict[str, Any]:
    """Aplana estructuras anidadas (dict o listas) en una única capa, prefijando claves."""
    output: Dict[str, Any] = {}
    if isinstance(value, dict):
        for key, val in value.items():
            output.update(flatten_json(val, f"{prefix}{key}_"))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            if isinstance(item, (dict, list)):
                output.update(flatten_json(item, f"{prefix}{idx}_"))
            else:
                output[f"{prefix}{idx}"] = item
    else:
        output[prefix[:-1]] = value
    return output

def normalize_array_of_pairs(
    arr: List[List[Any]], base: Dict[str, Any], prefix: str
) -> List[Dict[str, Any]]:
    """
    Transforma un array de pares [[x, y], [a, b]] en filas SQL con claves separadas.
    Incluye el símbolo de origen.
    """
    rows: List[Dict[str, Any]] = []
    for item in arr:
        if isinstance(item, list) and len(item) == 2:
            rows.append({
                "symbol_id": base["symbol_id"],
                "symbol": base["symbol"],
                f"{prefix}_x": json.dumps(item[0]),
                f"{prefix}_y": json.dumps(item[1]),
            })
    return rows

def process_field(
    value: Any,
    key: str,
    base: Dict[str, Any],
    rows_dict: Dict[str, List[Dict[str, Any]]],
    table_prefix: str,
    schema_local: Dict[str, Any]
) -> None:
    """
    Procesa un campo individual del símbolo (dict o lista), lo aplana o transforma,
    y lo inserta en el diccionario que acumula las filas relacionales por tabla.
    """
    table_name = f"{table_prefix}_sym_{key}"

    if isinstance(value, dict):
        flat_val = flatten_json(value)
        flat_val = {k: v for k, v in flat_val.items() if k in schema_local[key]}
        flat_val.update(base)
        rows_dict[table_name].append(flat_val)

    elif isinstance(value, list):
        if all(isinstance(i, list) and len(i) == 2 for i in value):
            rows_dict[table_name].extend(normalize_array_of_pairs(value, base, key))
        else:
            safe_array = {f"{key}_{i}": json.dumps(v) for i, v in enumerate(value)}
            rows_dict[table_name].append({**base, **safe_array})

# ---------------------------------------------------------------------------
# 3. Construir diccionario relacional para campos anidados
# ---------------------------------------------------------------------------

def build_relational_rows(
    exchange: ccxt.Exchange,
    symbols: List[str],
    schema_local: Dict[str, Any],
    exchange_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Construye una estructura de tablas y filas relacionales a partir de todos los símbolos,
    extrayendo únicamente los campos que están definidos como estructuras complejas en el schema.
    """
    rows_relacionales: Dict[str, List[Dict[str, Any]]] = {
        f"{exchange_id}_sym_{key}": []
        for key in schema_local
        if isinstance(schema_local[key], (dict, list))
    }

    print(f"🔁 Procesando {len(symbols)} símbolos de {exchange_id}…")

    for symbol in symbols:
        try:
            market = exchange.markets[symbol]
            base_ref = {"symbol_id": f"{exchange_id}:{symbol}", "symbol": symbol}

            for key in schema_local:
                if key in {"symbol_id", "symbol"}:
                    continue
                value = market.get(key)
                if isinstance(schema_local[key], (dict, list)):
                    process_field(value, key, base_ref, rows_relacionales, exchange_id, schema_local)
        except Exception as exc:
            print(f"⚠️ Error con símbolo {symbol}: {exc}")

    return rows_relacionales

# ---------------------------------------------------------------------------
# 4. Crear e insertar tablas relacionales en MariaDB
# ---------------------------------------------------------------------------

def create_and_fill_relational_tables(
    connection: pymysql.connections.Connection,
    rows_dict: Dict[str, List[Dict[str, Any]]]
) -> None:
    """
    A partir del diccionario de filas por tabla, crea las tablas si no existen
    y realiza un `REPLACE INTO` para evitar duplicados. Todo queda limpio.
    """
    for table, rows in rows_dict.items():
        if not rows:
            continue

        df = pd.DataFrame(rows).where(pd.notnull(pd.DataFrame(rows)), None).replace({np.nan: None})
        df.columns = [sanitize_name(col).strip("`") for col in df.columns]

        cols_sql_parts = [
            f"`{col}` VARCHAR(255)" if col in {"symbol_id", "symbol"} else f"`{col}` TEXT"
            for col in df.columns
        ]
        primary_keys = [key for key in ("symbol_id", "symbol") if key in df.columns]
        if primary_keys:
            cols_sql_parts.append("PRIMARY KEY (" + ", ".join(f"`{key}`" for key in primary_keys) + ")")

        create_sql = (
            f"CREATE TABLE IF NOT EXISTS `{table}` (\n    "
            + ",\n    ".join(cols_sql_parts)
            + "\n) CHARACTER SET utf8mb4;"
        )
        insert_sql = (
            f"REPLACE INTO `{table}` (" + ", ".join(f"`{col}`" for col in df.columns) + ") "
            f"VALUES ({', '.join(['%s'] * len(df.columns))});"
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(create_sql)
                cursor.executemany(insert_sql, df.values.tolist())
            connection.commit()
            print(f"✅ Tabla `{table}` creada e insertada sin duplicados.")
        except Exception as exc:
            print(f"⚠️ Error en tabla {table}: {exc}")

# ---------------------------------------------------------------------------
# 5. Crear tabla plana con todos los símbolos (sin anidamiento)
# ---------------------------------------------------------------------------

def create_flat_symbols_table(
    connection: pymysql.connections.Connection,
    exchange_id: str,
    exchange: ccxt.Exchange,
    schema_local: Dict[str, Any],
    symbols: List[str]
) -> None:
    """
    Crea la tabla `<exchange>_sym_symbols` con una fila por símbolo,
    conteniendo solo campos simples (no listas ni dicts).
    """
    table_name = f"{exchange_id}_sym_symbols"
    rows = []

    for symbol in symbols:
        try:
            market = exchange.markets[symbol]
            row = {"symbol_id": f"{exchange_id}:{symbol}", "symbol": symbol}
            for key, value in market.items():
                if key in schema_local and not isinstance(schema_local[key], (dict, list)):
                    row[key] = value
            rows.append(row)
        except Exception as exc:
            print(f"⚠️ Error procesando {symbol} en tabla plana: {exc}")

    if not rows:
        print(f"⚠️ No se generaron datos para {table_name}")
        return

    df = pd.DataFrame(rows).where(pd.notnull(pd.DataFrame(rows)), None).replace({np.nan: None})
    df.columns = [sanitize_name(col).strip("`") for col in df.columns]

    cols_sql_parts = [
        f"`{col}` VARCHAR(255)" if col in {"symbol_id", "symbol"} else f"`{col}` TEXT"
        for col in df.columns
    ]
    primary_keys = [key for key in ("symbol_id", "symbol") if key in df.columns]
    if primary_keys:
        cols_sql_parts.append("PRIMARY KEY (" + ", ".join(f"`{key}`" for key in primary_keys) + ")")

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
        print(f"✅ Tabla `{table_name}` creada e insertada con datos planos.")
    except Exception as exc:
        print(f"⚠️ Error creando o insertando en {table_name}: {exc}")

# ---------------------------------------------------------------------------
# 6. Entrada principal: orquesta todo el proceso
# ---------------------------------------------------------------------------

def main() -> None:
    exchange_id = "kraken"

    # Cargar el schema mínimo previamente generado (solo campos relevantes)
    try:
        schema_module = importlib.import_module(f"schemas.{exchange_id}.{exchange_id}_schema_taker_min")
    except ModuleNotFoundError:
        raise RuntimeError(f"❌ No se pudo importar el schema mínimo de `{exchange_id}`.")

    schema_local: Dict[str, Any] = schema_module.schema

    # Instanciar el exchange y cargar sus mercados
    try:
        exchange = getattr(ccxt, exchange_id)()
        exchange.load_markets()
    except Exception as exc:
        raise RuntimeError(f"❌ Error al cargar exchange {exchange_id}: {exc}") from exc

    symbols: List[str] = exchange.symbols  # Lista completa de símbolos (pares)

    # Conexión con la base de datos
    connection = pymysql.connect(**DB_CONFIG)

    try:
        rows_relacionales = build_relational_rows(exchange, symbols, schema_local, exchange_id)
        create_and_fill_relational_tables(connection, rows_relacionales)
        create_flat_symbols_table(connection, exchange_id, exchange, schema_local, symbols)
    finally:
        connection.close()

    print("🎯 Finalizado.")

if __name__ == "__main__":
    main()
