# app/codigo/4_generar_tabla_unificada.py
import os
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from functools import reduce
from config.db import connect
from config.config import STATIC_DIR, DATOS_DIR
import importlib.util

# 📌 Cargar referencia_tabla_unica
ref_path = STATIC_DIR / "referencia_tabla_unica.py"
spec = importlib.util.spec_from_file_location("referencia_tabla_unica", ref_path)
ref_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref_module)
schema_unificado = getattr(ref_module, "schema_unificado")

TABLA_DESTINO = "tabla_unica"

def generar_tabla_unificada():
    from config.db import get_db_config

    db_conf = get_db_config()
    pw_escaped = (db_conf['password'] or "").replace("@", "%40")  # escapamos @
    engine = create_engine(
        f"mysql+pymysql://{db_conf['user']}:{pw_escaped}@{db_conf['host']}/{db_conf['database']}"
    )
    conn = connect()


    dataframes = []
    for tabla, columnas in schema_unificado.items():
        query = f"SELECT {', '.join(f'`{c}`' for c in columnas)} FROM `{tabla}`"
        df = pd.read_sql(query, engine)
        dataframes.append(df)

    df_final = reduce(lambda left, right: pd.merge(left, right, on=["symbol_id", "symbol"]), dataframes)

    # Drop tabla previa si existe
    with conn.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS `{TABLA_DESTINO}`;")

        cols_sql = ",\n    ".join([
            f"`{col}` VARCHAR(255)" if col in ['symbol_id','symbol','base','quote','type'] else f"`{col}` TEXT"
            for col in df_final.columns
        ])
        create_stmt = f"""
            CREATE TABLE `{TABLA_DESTINO}` (
                {cols_sql},
                PRIMARY KEY (`symbol_id`)
            ) CHARACTER SET utf8mb4;
        """
        cursor.execute(create_stmt)

        insert_sql = f"INSERT INTO `{TABLA_DESTINO}` ({', '.join(f'`{c}`' for c in df_final.columns)}) VALUES ({', '.join(['%s'] * len(df_final.columns))});"
        for _, row in df_final.iterrows():
            cursor.execute(insert_sql, row.tolist())

        conn.commit()

    # Export CSV
    output_dir = DATOS_DIR / "tratamiento_de_tablas"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{TABLA_DESTINO}.csv"
    df_final.to_csv(csv_path, index=False)

    print(f"✅ Tabla `{TABLA_DESTINO}` creada en DB con {len(df_final)} registros.")
    print(f"📄 CSV exportado en {csv_path}")

    conn.close()

if __name__ == "__main__":
    generar_tabla_unificada()
