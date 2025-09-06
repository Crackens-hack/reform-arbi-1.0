# 1_generar_schemas.py
# pylint: disable=invalid-name
"""
Genera un archivo de *schema* estructural basado en todos los mercados que
retorna `load_markets()` de CCXT para Kraken.

🗂  Salida:
   - El schema se guarda en: `codigo/schemas/kraken/kraken_schema.py`
"""

import json
from pathlib import Path
from typing import Any
import ccxt

# ---------------------------------------------------------------------------
# 📁 Definición de rutas base
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent  # Ruta absoluta al directorio del script actual (/codigo/)
SCHEMAS_BASE_DIR = BASE_DIR / "schemas"     # Subcarpeta donde se guardarán los schemas

# ---------------------------------------------------------------------------
# 🔧 Funciones utilitarias para inferencia y manejo estructural
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
        if all(isinstance(i, (str, int, float, bool)) for i in value):
            return f"[{infer_type(value[0])}]"
        return "[any]"  # Lista de elementos diversos
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
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

# ---------------------------------------------------------------------------
# 🚀 Función principal: genera schema para Kraken
# ---------------------------------------------------------------------------

def generate_schema() -> None:
    """
    Crea el archivo de schema para Kraken basado en `exchange.markets`,
    infiriendo los tipos de datos y exportándolo como archivo .py estructurado.
    """
    exchange_id = "kraken"
    try:
        # Inicializa exchange desde CCXT
        exchange = getattr(ccxt, exchange_id)()
        exchange.load_markets()  # Carga info de todos los mercados disponibles

        schema: dict[str, Any] = {}

        # Recorrer todos los mercados para inferir y fusionar estructura
        for market in exchange.markets.values():
            inferred = infer_type(market)
            if isinstance(inferred, dict):
                schema = merge_dicts(schema, inferred)

        # Crear estructura de carpetas
        SCHEMAS_BASE_DIR.mkdir(exist_ok=True)
        ensure_init(SCHEMAS_BASE_DIR)

        exchange_dir = SCHEMAS_BASE_DIR / exchange_id
        exchange_dir.mkdir(exist_ok=True)
        ensure_init(exchange_dir)

        # Guardar como archivo Python con el schema
        output_path = exchange_dir / f"{exchange_id}_schema.py"
        with output_path.open("w", encoding="utf-8") as f:
            f.write(f"# Auto‑generado: estructura completa para el exchange '{exchange_id}'.\n")
            f.write("\nschema = ")
            json.dump(schema, f, indent=4, ensure_ascii=False)  # Escribe el schema como dict Python

        print(f"✅ Schema generado en: {output_path}")

    except (ccxt.NetworkError, ccxt.ExchangeError) as err:
        print(f"⚠️ Error procesando Kraken: {err}")

# ---------------------------------------------------------------------------
# ⏩ Punto de entrada (si se ejecuta como script)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    generate_schema()
