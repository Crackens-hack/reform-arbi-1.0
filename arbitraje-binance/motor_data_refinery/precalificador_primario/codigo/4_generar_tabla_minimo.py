# ---------------------------------------------------------------------------
# 📦 Importaciones necesarias
# ---------------------------------------------------------------------------
import os
import sys
import pymysql
import pandas as pd
from sqlalchemy import create_engine
import importlib.util

# ---------------------------------------------------------------------------
# 📌 Punto raíz fijo como si estuviéramos en 'codigo/'
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Ruta absoluta al directorio actual
EXCHANGE_ID = "kraken"  # 🔒 Exchange fijo para este script

# ---------------------------------------------------------------------------
# 🔐 Configuración de la base de datos (desde variables de entorno)
# ---------------------------------------------------------------------------
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# ---------------------------------------------------------------------------
# 📥 Cargar el diccionario mínimo de campos desde archivo dinámico
# ---------------------------------------------------------------------------
def cargar_diccionario_minimo(exchange_id):
    """
    Carga dinámicamente el archivo Python con los campos mínimos necesarios
    para crear una tabla estructural mínima del exchange.

    Ejemplo esperado: campos_necesarios/kraken/kraken_minimo.py
    con una variable llamada `KRAKEN_MINIMO`.
    """
    path = os.path.join(BASE_DIR, "campos_necesarios", exchange_id, f"{exchange_id}_minimo.py")

    if not os.path.exists(path):
        print(f"❌ Diccionario mínimo no encontrado: {path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("minimo_module", path)
    minimo_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(minimo_module)

    nombre_var = f"{exchange_id.upper()}_MINIMO"
    if not hasattr(minimo_module, nombre_var):
        print(f"❌ La variable '{nombre_var}' no está definida dentro de {path}.")
        sys.exit(1)

    return getattr(minimo_module, nombre_var)

# ---------------------------------------------------------------------------
# 🏗 Generador principal de tabla mínima
# ---------------------------------------------------------------------------
def generar_tabla_minimo(exchange_id):
    tabla_destino = f"{exchange_id}_minimo"

    try:
        # 🔌 Conexión directa a la DB y vía SQLAlchemy para pandas
        conn = pymysql.connect(**DB_CONFIG)

        # 🔐 Escapar '@' en la password para que la URI de SQLAlchemy funcione
        pw_escaped = DB_CONFIG['password'].replace('@', '%40')

        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{pw_escaped}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

        # 📄 Cargar los campos por tabla definidos para este exchange
        campos_por_tabla = cargar_diccionario_minimo(exchange_id)
        dataframes = []

        # 🧩 Armar DataFrames parciales por cada tabla involucrada
        for tabla_base, columnas in campos_por_tabla.items():
            columnas_str = ", ".join(f"`{c}`" for c in columnas)
            query = f"SELECT {columnas_str} FROM {tabla_base}"
            df = pd.read_sql(query, engine)
            dataframes.append(df)

        # 🔗 Unir todos los DataFrames usando symbol_id y symbol como claves
        from functools import reduce
        df_final = reduce(lambda left, right: pd.merge(left, right, on=["symbol_id", "symbol"]), dataframes)

        # 🧨 Borrar tabla destino si ya existe
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS `{tabla_destino}`;")

            # 🧱 Crear definición SQL de columnas (VARCHAR o TEXT según tipo)
            columnas_sql = ",\n    ".join([
                f"`{col}` VARCHAR(255)" if col in ['symbol_id', 'symbol', 'base', 'quote'] else f"`{col}` TEXT"
                for col in df_final.columns
            ])

            # 🏗 Crear tabla con PRIMARY KEY en symbol_id
            create_stmt = f"""
                CREATE TABLE `{tabla_destino}` (
                    {columnas_sql},
                    PRIMARY KEY (`symbol_id`)
                ) CHARACTER SET utf8mb4;
            """
            cursor.execute(create_stmt)

            # ➕ Insertar registros uno por uno
            insert_sql = f"INSERT INTO `{tabla_destino}` ({', '.join(f'`{c}`' for c in df_final.columns)}) VALUES ({', '.join(['%s'] * len(df_final.columns))});"
            for _, row in df_final.iterrows():
                cursor.execute(insert_sql, row.tolist())

            conn.commit()

        # 📁 Crear carpeta de salida si no existe
        output_dir = os.path.join(BASE_DIR, "datos", exchange_id)
        os.makedirs(output_dir, exist_ok=True)

        # 📝 Guardar archivo TXT con los campos utilizados por tabla
        with open(os.path.join(output_dir, f"{tabla_destino}.txt"), "w", encoding="utf-8") as f:
            f.write(f"# Campos usados para {tabla_destino}:\n\n")
            for tabla, campos in campos_por_tabla.items():
                f.write(f"[{tabla}]\n")
                for campo in campos:
                    f.write(f"  - {campo}\n")
                f.write("\n")

        # 📤 Exportar CSV final con todos los campos unificados
        csv_path = os.path.join(output_dir, f"{tabla_destino}.csv")
        df_final.to_csv(csv_path, index=False)

        # ✅ Mensajes finales
        print(f"\n✅ Tabla `{tabla_destino}` generada correctamente con {len(df_final)} registros.")
        print(f"📄 CSV exportado en: {csv_path}")
        print(f"📝 TXT exportado en: datos/{exchange_id}/{tabla_destino}.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error generando la tabla mínima: {e}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# 🚀 Ejecución
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    generar_tabla_minimo(EXCHANGE_ID)
