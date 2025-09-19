# codigo/config/config.py
"""
Config centralizada para el pipeline (Docker-friendly).
"""

from __future__ import annotations
from pathlib import Path
import importlib.util

# ─────────── Rutas base ───────────
CODIGO_DIR = Path(__file__).resolve().parents[1]     # .../<repo>/codigo
APP_DIR    = CODIGO_DIR.parent                       # .../<repo>
TEMP_DIR   = CODIGO_DIR / "temp"
STATIC_DIR = CODIGO_DIR / "static"
DATOS_DIR  = CODIGO_DIR / "datos"
ESTRUCTURAL_DIR = DATOS_DIR / "estructural"

def ensure_runtime_dirs() -> None:
    """Crea carpetas necesarias para importar módulos y exportar auditoría."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    (TEMP_DIR / "__init__.py").touch(exist_ok=True)
    DATOS_DIR.mkdir(parents=True, exist_ok=True)
    ESTRUCTURAL_DIR.mkdir(parents=True, exist_ok=True)

# ─────────── Exchange / CCXT ───────────
EXCHANGE_ID = "binance"
CCXT_OPTIONS = {
    "enableRateLimit": True,
    "timeout": 20_000,
    "options": {"adjustForTimeDifference": True},
}

# ─────────── Fuentes de schema ───────────
# Obligatorio: schema manual estable
SCHEMA_PRIMARY_PATH = STATIC_DIR / "schema_funcional.py"
# Temporal (lo usa el paso 1; NO es fallback en este script)
SCHEMA_OUTPUT_PATH  = TEMP_DIR / "schema.py"

# ─────────── Auditoría (export CSV de estructura) ───────────
AUDIT_STRUCT_EXPORT = True  # ponelo en False si no querés CSVs en datos/estructural/

def _import_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"❌ No pude crear spec para importar: {path}")
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

def load_schema_or_abort():
    """
    Carga y devuelve el dict `schema` desde codigo/static/schema_funcional.py.
    Si no existe o no exporta `schema`, aborta (no hay fallback a temp).
    """
    if not SCHEMA_PRIMARY_PATH.exists():
        raise RuntimeError(
            f"❌ Falta el schema manual: {SCHEMA_PRIMARY_PATH}\n"
            f"   Generá/validá tu schema estable antes de continuar."
        )
    mod = _import_module_from_path(SCHEMA_PRIMARY_PATH)
    if not hasattr(mod, "schema"):
        raise RuntimeError(f"❌ `{SCHEMA_PRIMARY_PATH.name}` no exporta la variable `schema`.")
    schema = getattr(mod, "schema")
    if not isinstance(schema, dict):
        raise RuntimeError(f"❌ `schema` debe ser dict en {SCHEMA_PRIMARY_PATH}.")
    return schema
