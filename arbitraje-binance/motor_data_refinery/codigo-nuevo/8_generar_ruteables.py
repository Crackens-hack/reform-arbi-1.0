# codigo/8_generar_ruteables.py
"""
Genera cotizaciones indirectas ruteables y no ruteables.
Usa config_cotizacion_indirecta.csv para saber qué tablas (CSV) usar:
- tabla_indirecta
- tabla_directa
- tabla_invertida
- interesado_en (ej: USDT)

Salida:
- datos/cotizaciones/ruteables_{interesado_en}.csv
- datos/cotizaciones/no_ruteables_{interesado_en}.csv  (si existen)
- datos/cotizaciones/no_ruteables_{interesado_en}.log  (si no existen)
"""

import pandas as pd
from decimal import Decimal, getcontext, InvalidOperation
from pathlib import Path

# Precisión alta
getcontext().prec = 50

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT_DIR / "codigo" / "static" / "config_cotizacion_indirecta.csv"

DATOS_DIR = ROOT_DIR / "codigo" / "datos"

def cargar_config():
    df = pd.read_csv(CONFIG_FILE)
    if df.empty:
        raise ValueError("❌ Config vacío")
    return {
        "tabla_indirecta": df.loc[0, "tabla_indirecta"],
        "tabla_directa": df.loc[0, "tabla_directa"],
        "tabla_invertida": df.loc[0, "tabla_invertida"],
        "interesado_en": df.loc[0, "interesado_en"].upper().strip(),
    }

def main():
    cfg = cargar_config()
    interesado = cfg["interesado_en"]

    base_path = DATOS_DIR / "tratamiento_de_cotizacion"
    f_indir = base_path / f"{cfg['tabla_indirecta']}.csv"
    f_dir   = base_path / f"{cfg['tabla_directa']}.csv"
    f_inv   = base_path / f"{cfg['tabla_invertida']}.csv"

    df_indir = pd.read_csv(f_indir, dtype=str)
    df_dir   = pd.read_csv(f_dir, dtype=str)
    df_inv   = pd.read_csv(f_inv, dtype=str)

    bases_directas = set(df_dir["base"].dropna().str.strip().str.upper())
    quotes_invertidas = set(df_inv["quote"].dropna().str.strip().str.upper())

    ruteables, no_ruteables = [], []

    for _, row in df_indir.iterrows():
        base = str(row["base"]).strip().upper()
        quote = str(row["quote"]).strip().upper()
        symbol = str(row["symbol"]).strip().upper()

        match_info = []
        origen = "NONE"

        # Caso: base engancha en directos → origen = indirecto
        if base in bases_directas:
            match_info.append(f"base:{base}")
            origen = "indirecto"
        else:
            match_info.append("base:NONE")

        # Caso: quote engancha en directos → origen = indirecto
        if quote in bases_directas:
            match_info.append(f"quote:{quote}")
            origen = "indirecto"
        # Caso: quote engancha en invertidos → origen = invertido
        elif quote in quotes_invertidas:
            match_info.append(f"quote:{quote}")
            origen = "invertido"
        else:
            match_info.append("quote:NONE")

        fila = {
            "symbol": symbol,
            "base": base,
            "quote": quote,
            "cotiza_vs_directo": "; ".join(match_info),
            "origen": origen,
            "1_base_equivale_x_quote": "",
            "1_quote_equivale_x_base": ""
        }

        try:
            precio = Decimal(str(row.get("1_base_equivale_x_quote", "")))
            if precio and precio != 0:
                fila["1_base_equivale_x_quote"] = str(precio)
                fila["1_quote_equivale_x_base"] = str(Decimal("1") / precio)
        except (InvalidOperation, ValueError, ZeroDivisionError):
            pass

        if origen != "NONE":
            ruteables.append(fila)
        else:
            no_ruteables.append(fila)

    # Guardar
    out_dir = DATOS_DIR / "cotizaciones"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ruteables siempre
    pd.DataFrame(ruteables).to_csv(out_dir / f"ruteables_{interesado}.csv", index=False)

    if no_ruteables:
        pd.DataFrame(no_ruteables).to_csv(out_dir / f"no_ruteables_{interesado}.csv", index=False)
    else:
        log_path = out_dir / f"no_ruteables_{interesado}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("✅ No se encontraron no-ruteables.\n")
            f.write("Todos los pares indirectos fueron ruteados correctamente.\n")

    print(f"✅ Ruteables: {len(ruteables)} | No ruteables: {len(no_ruteables)}")
    print(f"📄 Archivos guardados en {out_dir}")

if __name__ == "__main__":
    main()
