# codigo/5_generar_tabla_funcional.py
# Genera la tabla kraken_funcional a partir de kraken_minimo
# Filtra por status online y elimina cualquier símbolo con fiat
# Guarda CSV funcional y CSV descartado dentro de codigo/datos/

# --- Importación de módulos necesarios ---
import os                   # Para manejo de rutas y archivos
import sys                  # Para poder hacer sys.exit() si ocurre un error
import pymysql              # Cliente MySQL/MariaDB para conexión directa
import pandas as pd         # Manejo de datos estructurados con DataFrames
from dotenv import load_dotenv        # Para cargar variables de entorno desde un archivo .env
from sqlalchemy import create_engine  # Para interactuar con la base de datos usando pandas
import importlib.util       # Para importar dinámicamente módulos (lista de tokens fiat en este caso)

# --- Definición del directorio base del script ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Carga de variables de entorno desde .env ---
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "..", ".env"))

# --- Configuración de conexión a base de datos usando valores del .env ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor  # Para que los resultados de consultas sean dicts
}

# --- Función que carga dinámicamente la lista de tokens fiat de un exchange específico ---
def cargar_lista_fiat(exchange_id):
    # Ruta del archivo que contiene la lista de tokens fiat
    path = os.path.join(BASE_DIR, "list_fiat", f"{exchange_id}_fiat.py")
    
    # Si el archivo no existe, muestra error y termina la ejecución
    if not os.path.exists(path):
        print(f"❌ Lista de fiat no encontrada: {path}")
        sys.exit(1)

    # Carga dinámica del módulo fiat usando importlib
    spec = importlib.util.spec_from_file_location("fiat_module", path)
    fiat_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fiat_module)

    # Retorna el conjunto de tokens fiat definidos en fiat_tokens
    return set(fiat_module.fiat_tokens)

# --- Función principal que genera la tabla funcional para Kraken ---
def generar_tabla_funcional():
    exchange_id = "kraken"                         # ID del exchange
    tabla_origen = f"{exchange_id}_minimo"         # Tabla base de origen
    tabla_destino = f"{exchange_id}_funcional"     # Tabla resultante a generar

    try:
        # Escapa el carácter '@' en la contraseña para armar la URI de SQLAlchemy
        pw_escaped = DB_CONFIG['password'].replace('@', '%40')

        # Crea el engine de SQLAlchemy para poder usar pandas.read_sql
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{pw_escaped}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

        # Conexión directa con PyMySQL para ejecutar queries manuales
        conn = pymysql.connect(**DB_CONFIG)

        # Carga toda la tabla origen en un DataFrame de pandas
        df = pd.read_sql(f"SELECT * FROM {tabla_origen}", engine)

        # Carga la lista de tokens fiat desde archivo
        fiat_tokens = cargar_lista_fiat(exchange_id)

        # Crea máscaras booleanas para detectar si el par involucra tokens fiat
        es_base_fiat = df["base"].isin(fiat_tokens)
        es_quote_fiat = df["quote"].isin(fiat_tokens)

        # Máscara para filtrar símbolos con status 'online'
        es_status_online = df["status"].str.lower() == "online"

        # Aplica filtros: excluye pares con fiat y que no estén online
        df_filtrado = df[~(es_base_fiat | es_quote_fiat) & es_status_online].copy()

        # Elimina la columna 'status' del resultado final
        df_filtrado.drop(columns=["status"], inplace=True)

        # Guarda aparte los símbolos descartados por tener fiat
        df_descartados = df[es_base_fiat | es_quote_fiat].copy()

        # Muestra cuántos símbolos cripto-cripto fueron encontrados
        print(f"🔎 Símbolos cripto-cripto funcionales: {len(df_filtrado)}")

        # Si no hay datos válidos, muestra advertencia y termina
        if df_filtrado.empty:
            print("⚠️ No se encontraron símbolos funcionales cripto-cripto.")
            return

        # --- Inicio de operaciones sobre la base de datos ---
        with conn.cursor() as cursor:
            # Elimina la tabla destino si ya existía
            cursor.execute(f"DROP TABLE IF EXISTS `{tabla_destino}`;")

            # Genera los campos SQL para la creación de la nueva tabla
            columnas_sql = ",\n    ".join([
                f"`{col}` VARCHAR(255)" if col in ['symbol_id', 'symbol', 'base', 'quote'] else f"`{col}` TEXT"
                for col in df_filtrado.columns
            ])

            # Ejecuta el SQL para crear la tabla nueva con las columnas generadas dinámicamente
            cursor.execute(f"""
                CREATE TABLE `{tabla_destino}` (
                    {columnas_sql},
                    PRIMARY KEY (`symbol_id`)
                ) CHARACTER SET utf8mb4;
            """)

            # Arma la sentencia SQL de inserción múltiple
            insert_sql = f"INSERT INTO `{tabla_destino}` ({', '.join(f'`{c}`' for c in df_filtrado.columns)}) VALUES ({', '.join(['%s'] * len(df_filtrado.columns))});"

            # Inserta cada fila del DataFrame en la tabla
            for _, row in df_filtrado.iterrows():
                cursor.execute(insert_sql, row.tolist())
            
            # Confirma los cambios en la base
            conn.commit()

        # --- Exportación a CSV ---
        output_dir = os.path.join(BASE_DIR, "datos", exchange_id)
        os.makedirs(output_dir, exist_ok=True)  # Crea el directorio si no existe

        # Exporta el DataFrame filtrado a CSV
        df_filtrado.to_csv(os.path.join(output_dir, f"{tabla_destino}.csv"), index=False)

        # Exporta los símbolos descartados por contener fiat
        df_descartados.to_csv(os.path.join(output_dir, f"{exchange_id}_descartados_fiat.csv"), index=False)

        # Mensajes finales informando éxito
        print(f"✅ Tabla `{tabla_destino}` generada con {len(df_filtrado)} símbolos.")
        print(f"📁 CSV funcional: codigo/datos/{exchange_id}/{tabla_destino}.csv")
        print(f"📁 CSV descartados: codigo/datos/{exchange_id}/{exchange_id}_descartados_fiat.csv")

        # Cierra la conexión con la base de datos
        conn.close()

    # --- Manejo de errores ---
    except Exception as e:
        # En caso de error, lo muestra y termina ejecución con código 1
        print(f"❌ Error generando la tabla funcional: {e}")
        sys.exit(1)

# --- Punto de entrada del script ---
if __name__ == '__main__':
    generar_tabla_funcional()
