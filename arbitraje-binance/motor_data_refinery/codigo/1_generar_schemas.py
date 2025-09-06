# app/codigo/1_generar_schemas.py
# pylint: disable=invalid-name
"""
Genera un archivo de *schema* estructural basado en todos los mercados que
retorna `load_markets()` de CCXT para el exchange definido en config.EXCHANGE_ID.

🗂  Salida:
   - El schema se guarda en: app/codigo/temp/schema.py  (sin prefijo de exchange)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import ccxt

# ---------------------------------------------------------------------------
# 🔗 Config centralizada (soporta ejecución como módulo o script)
# ---------------------------------------------------------------------------
try:
    # cuando corrés: python -m app.codigo.1_generar_schemas
    from .config import config
except Exception:
    # cuando corrés: python app/codigo/1_generar_schemas.py
    import sys, os
    THIS_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(THIS_DIR / "config"))   # app/codigo/config
    sys.path.insert(0, str(THIS_DIR))              # app/codigo
    import config  # type: ignore

# ---------------------------------------------------------------------------
# 🔧 Utilitarios de inferencia/estructura
# ---------------------------------------------------------------------------

def infer_type(value: Any) -> Any:
    """
    Infiero el tipo de dato de un valor, recursivamente si es lista o dict.
    Devuelve una descripción simple del tipo, como "str", "int", "[str]", etc.
    """
    if isinstance(value, str): return "str"
    if isinstance(value, bool): return "bool"
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, list):
        # Si es una lista de pares tipo [[a, b], [c, d]], se detecta como lista de tuplas
        if all(isinstance(i, list) and len(i) == 2 for i in value):
            return "[[any, any]]"
        # Si todos los elementos son tipos simples
        if len(value) > 0 and all(isinstance(i, (str, int, float, bool)) for i in value):
            return f"[{infer_type(value[0])}]"
        return "[any]"  # Lista de elementos diversos o vacía
    if isinstance(value, dict):
        # Inferir estructura interna de diccionarios
        return {k: infer_type(v) for k, v in value.items()}
    if value is None:
        return "None"
    return "any"

def merge_dicts(base: dict, new: dict) -> dict:
    """
    Une dos diccionarios recursivamente. Preserva las claves existentes,
    y extiende estructuras anidadas si ambas claves son dicts.
    """
    for key, new_val in new.items():
        if key not in base:
            base[key] = new_val
        elif isinstance(base[key], dict) and isinstance(new_val, dict):
            base[key] = merge_dicts(base[key], new_val)
    return base

def ensure_init(path: Path) -> None:
    """
    Asegura que el directorio tenga un __init__.py para hacerlo importable como módulo.
    """
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

# ---------------------------------------------------------------------------
# 🚀 Generador principal (config-driven)
# ---------------------------------------------------------------------------

def generate_schema() -> None:
    """
    Crea el archivo de schema basado en `exchange.markets`,
    infiriendo los tipos de datos y exportándolo como archivo .py estructurado.
    Usa EXCHANGE_ID y SCHEMA_OUTPUT_PATH desde config.
    """
    exchange_id = config.EXCHANGE_ID
    output_path: Path = Path(config.SCHEMA_OUTPUT_PATH)

    # Asegurar carpeta temp y que sea importable
    if hasattr(config, "ensure_runtime_dirs"):
        config.ensure_runtime_dirs()
    else:
        ensure_init(output_path.parent)

    try:
        # Inicializa exchange desde CCXT con opciones de config
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class(config.CCXT_OPTIONS)
        exchange.load_markets()  # Carga info de todos los mercados disponibles

        schema: dict[str, Any] = {}

        # Recorrer todos los mercados para inferir y fusionar estructura
        for market in exchange.markets.values():
            inferred = infer_type(market)
            if isinstance(inferred, dict):
                schema = merge_dicts(schema, inferred)

        # Guardar como archivo Python con el schema (sin prefijo del exchange)
        with output_path.open("w", encoding="utf-8") as f:
            f.write("# Auto-generado: estructura completa deducida desde CCXT.\n")
            f.write(f"# Exchange origen: {exchange_id}\n")
            f.write("# Origen del generador: app/codigo/1_generar_schemas.py\n\n")
            f.write("schema = ")
            json.dump(schema, f, indent=4, ensure_ascii=False)  # Dict Python serializado

        print(f"✅ Schema generado en: {output_path}")

    except AttributeError:
        print(f"❌ Exchange '{exchange_id}' no es reconocido por CCXT.")
    except (ccxt.NetworkError, ccxt.ExchangeError) as err:
        print(f"⚠️ Error procesando '{exchange_id}' vía CCXT: {err}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

# ---------------------------------------------------------------------------
# ⏩ Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    generate_schema()
