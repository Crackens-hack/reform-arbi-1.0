# codigo/5_generar_tabla_funcional.py
"""
Genera tabla funcional a partir de tabla_unica.csv según reglas declaradas.
- Aplica criterios desde static/criterios_filtrados.csv
- Usa fiat_tokens de static/fiat.py para descartar pares fiat
- Exporta resultados:
  - funcional_<OUTPUT>.csv
  - descartados_<OUTPUT>.csv (con motivo_descartado)
  - Tablas en DB: funcional_<OUTPUT>, descartados_<OUTPUT>
en app/codigo/datos/tratamiento_de_tablas/
"""

import sys
from pathlib import Path
import pandas as pd

# ─────────── Fix path para que 'codigo' sea importable ───────────
APP_DIR = Path(__file__).resolve().parents[1]  # /app
sys.path.insert(0, str(APP_DIR))

# Config centralizada
from codigo.config import DATOS_DIR
from codigo.static.fiat import fiat_tokens   # lista global de FIAT
from codigo.config.db import connect         # función para conectar DB

# ─────────── Rutas de entrada / salida ───────────
TRATAMIENTO_DIR = DATOS_DIR / "tratamiento_de_tablas"
INPUT_PATH = TRATAMIENTO_DIR / "tabla_unica.csv"
CRITERIOS_PATH = APP_DIR / "codigo" / "static" / "criterios_filtrados.csv"


# ─────────── Helpers ───────────

def _normalizar_valor(valor: str) -> str:
    """
    Normaliza valores para comparar contra criterios.
    - True equivalentes: "true", "1", "yes"
    - False equivalentes: "false", "0", "no"
    - Todo lo demás: upper
    """
    v = str(valor).strip().lower()
    if v in {"true", "1", "yes"}:
        return "TRUE"
    if v in {"false", "0", "no"}:
        return "FALSE"
    return v.upper()


# ─────────── Funciones principales ───────────

def cargar_tabla_unica() -> pd.DataFrame:
    """Carga la tabla_unica.csv como DataFrame (todo string por seguridad)."""
    if not INPUT_PATH.exists():
        print(f"❌ No se encontró el archivo de entrada: {INPUT_PATH}")
        sys.exit(1)
    return pd.read_csv(INPUT_PATH, dtype=str)


def cargar_criterios() -> tuple[dict[str, set[str]], str]:
    """
    Lee el archivo CSV de criterios y devuelve:
    - dict campo→valores_permitidos
    - nombre de salida (sufijo) definido en __OUTPUT__
    """
    if not CRITERIOS_PATH.exists():
        print(f"❌ No existe el archivo de criterios: {CRITERIOS_PATH}")
        sys.exit(1)

    df = pd.read_csv(CRITERIOS_PATH, dtype=str)
    criterios = {}
    output_name = "default"

    for _, row in df.iterrows():
        campo = str(row["campo"]).strip()
        permitidos = str(row["permitidos"]).strip()
        if campo == "__OUTPUT__":
            output_name = permitidos
            continue
        if permitidos:
            criterios[campo] = {_normalizar_valor(v) for v in permitidos.split(";")}
    return criterios, output_name


def aplicar_criterios(df: pd.DataFrame, criterios: dict[str, set[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filtra df según criterios declarativos; devuelve (funcional, descartados)."""
    funcional = []
    descartados = []

    fiat_norm = {t.upper() for t in fiat_tokens}

    for _, row in df.iterrows():
        valido = True
        motivo = []

        for campo, permitidos in criterios.items():
            if campo not in row:
                continue

            valor = _normalizar_valor(row[campo])

            # Caso especial: NOT_FIAT
            if "NOT_FIAT" in permitidos:
                if valor in fiat_norm:
                    valido = False
                    motivo.append(f"{campo}=FIAT")
            else:
                if valor not in permitidos:
                    valido = False
                    motivo.append(f"{campo}='{valor}' no permitido")

        if valido:
            funcional.append(row)
        else:
            row_copy = row.copy()
            row_copy["motivo_descartado"] = "; ".join(motivo)
            descartados.append(row_copy)

    return pd.DataFrame(funcional), pd.DataFrame(descartados)


def guardar_resultados_csv(df_funcional: pd.DataFrame, df_descartados: pd.DataFrame,
                           criterios: dict[str, set[str]], output_name: str) -> None:
    """Guarda los dos DataFrames en CSV en la carpeta de tratamiento_de_tablas.
       Elimina columnas irrelevantes (ej. swap/future/option=FALSE)."""
    TRATAMIENTO_DIR.mkdir(parents=True, exist_ok=True)

    # Columnas que pediste siempre en FALSE → eliminamos
    columnas_a_quitar = [campo for campo, vals in criterios.items() if vals == {"FALSE"}]

    if columnas_a_quitar:
        df_funcional = df_funcional.drop(columns=[c for c in columnas_a_quitar if c in df_funcional.columns])
        df_descartados = df_descartados.drop(columns=[c for c in columnas_a_quitar if c in df_descartados.columns])

    out_funcional = TRATAMIENTO_DIR / f"funcional_{output_name}.csv"
    out_descartados = TRATAMIENTO_DIR / f"descartados_{output_name}.csv"

    df_funcional.to_csv(out_funcional, index=False)
    df_descartados.to_csv(out_descartados, index=False)

    print("✅ CSVs guardados:")
    print(f"   📄 {out_funcional}")
    print(f"   📄 {out_descartados}")


def guardar_en_db(df: pd.DataFrame, table_name: str, criterios: dict[str, set[str]]) -> None:
    """Crea/llena tabla en la DB con los resultados filtrados."""
    if df.empty:
        print(f"⚠️ No hay datos para {table_name}, se omite creación.")
        return

    # Columnas irrelevantes (FALSE) no se guardan
    columnas_a_quitar = [campo for campo, vals in criterios.items() if vals == {"FALSE"}]
    df = df.drop(columns=[c for c in columnas_a_quitar if c in df.columns])

    # Reemplazar NaN por None (→ NULL en SQL)
    df = df.where(pd.notnull(df), None)

    cols = df.columns.tolist()

    # Definir tipos: claves identificadoras en VARCHAR, resto en TEXT
    col_defs = []
    for c in cols:
        if c in {"symbol_id", "symbol", "base", "quote"}:
            col_defs.append(f"`{c}` VARCHAR(255)")
        else:
            col_defs.append(f"`{c}` TEXT")

    pk = "symbol_id" if "symbol_id" in cols else cols[0]

    create_sql = f"""
        CREATE TABLE `{table_name}` (
            {", ".join(col_defs)},
            PRIMARY KEY (`{pk}`)
        ) CHARACTER SET utf8mb4;
    """

    insert_sql = f"""
        INSERT INTO `{table_name}` ({", ".join(f"`{c}`" for c in cols)})
        VALUES ({", ".join(['%s']*len(cols))});
    """

    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`;")
            cursor.execute(create_sql)
            cursor.executemany(insert_sql, df.values.tolist())
        conn.commit()
        print(f"✅ Datos guardados en DB: `{table_name}` ({len(df)} filas).")
    finally:
        conn.close()


def generar_tabla_funcional():
    df = cargar_tabla_unica()
    criterios, output_name = cargar_criterios()

    df_funcional, df_descartados = aplicar_criterios(df, criterios)

    print(f"🔎 Funcionales: {len(df_funcional)} | Descartados: {len(df_descartados)}")

    # Guardar en CSV
    guardar_resultados_csv(df_funcional, df_descartados, criterios, output_name)

    # Guardar en DB
    guardar_en_db(df_funcional, f"funcional_{output_name}", criterios)
    guardar_en_db(df_descartados, f"descartados_{output_name}", criterios)


# ─────────── Main ───────────

if __name__ == "__main__":
    generar_tabla_funcional()
