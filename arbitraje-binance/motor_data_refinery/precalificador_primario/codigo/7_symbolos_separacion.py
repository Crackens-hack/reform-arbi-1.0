import os  # Módulo para interactuar con variables de entorno del sistema
import pymysql  # Cliente MySQL para Python
import pandas as pd  # Biblioteca para manipulación de datos en estructuras tipo DataFrame

# ⚙️ Configuración de la conexión a la base de datos usando variables de entorno
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),        # Dirección del host, por defecto 'localhost'
    "user": os.getenv("DB_USER", "root"),             # Usuario de la base, por defecto 'root'
    "password": os.getenv("DB_PASSWORD", ""),         # Contraseña del usuario, por defecto cadena vacía
    "database": os.getenv("DB_NAME", ""),             # Nombre de la base, por defecto cadena vacía
    "charset": "utf8mb4",                             # Charset usado, para soportar caracteres especiales
    "cursorclass": pymysql.cursors.DictCursor,        # Cursor que devuelve resultados en formato diccionario
}

# 🧩 Se establece la conexión a la base con los datos anteriores
connection = pymysql.connect(**DB_CONFIG)
cursor = connection.cursor()  # Se obtiene un cursor para ejecutar queries

# 📥 Consulta: se extraen los símbolos disponibles con sus pares base y quote
cursor.execute("SELECT symbol, base, quote FROM kraken_funcional")
rows = cursor.fetchall()  # Se obtienen todos los resultados
df = pd.DataFrame(rows)  # Se convierte en un DataFrame de Pandas para facilitar la manipulación

# 🔢 Se cuenta la cantidad total de símbolos originales
total_original = len(df)
print(f"🔍 Total de símbolos en kraken_funcional: {total_original}")

# 🧮 Clasificación de los pares según su relación con USDT:
# - directos: pares donde el quote es USDT (ej: BTC/USDT)
# - invertidos: pares donde el base es USDT (ej: USDT/BTC)
# - indirectos: pares donde ni el base ni el quote es USDT
directo = df[df['quote'] == 'USDT']
invertido = df[df['base'] == 'USDT']
indirecto = df[(df['base'] != 'USDT') & (df['quote'] != 'USDT')]

# 🛠️ Función para crear y poblar una tabla con los datos correspondientes
def manejar_tabla(nombre_tabla, datos):
    # 🧨 Borra la tabla si ya existía, para evitar conflictos
    cursor.execute(f"DROP TABLE IF EXISTS {nombre_tabla}")
    
    # ✅ Si hay datos, se crea y se insertan las filas
    if not datos.empty:
        # 🧱 Se crea la estructura de la tabla
        cursor.execute(
            f"""
            CREATE TABLE {nombre_tabla} (
                symbol VARCHAR(50),
                base VARCHAR(20),
                quote VARCHAR(20)
            )
            """
        )
        # ➕ Se insertan todos los registros fila por fila
        for _, row in datos.iterrows():
            cursor.execute(
                f"INSERT INTO {nombre_tabla} (symbol, base, quote) VALUES (%s, %s, %s)",
                (row['symbol'], row['base'], row['quote'])
            )
    else:
        # ⚠️ Si el DataFrame está vacío, se notifica que no se crea la tabla
        print(f"⚠️ Tabla vacía: {nombre_tabla}, no se creó.")

# 🚀 Se ejecuta la función para cada uno de los tres tipos de cotización
manejar_tabla("cotizador_directo", directo)
manejar_tabla("cotizador_invertido", invertido)
manejar_tabla("cotizador_indirecto", indirecto)

# 💾 Se confirman los cambios en la base de datos
connection.commit()

# 📊 Conteo de registros por categoría para verificar que no se perdió ningún símbolo
cant_directo = len(directo)
cant_invertido = len(invertido)
cant_indirecto = len(indirecto)
total_final = cant_directo + cant_invertido + cant_indirecto

# 📈 Se imprimen los resultados
print(f"✔ cotizador_directo: {cant_directo}")
print(f"✔ cotizador_invertido: {cant_invertido}")
print(f"✔ cotizador_indirecto: {cant_indirecto}")
print(f"📊 Total distribuido: {total_final}")

# ✅ Validación final: se compara el total original con el total final
if total_original == total_final:
    print("✅ Todos los símbolos fueron clasificados correctamente.")
else:
    print("❌ ERROR: Hay símbolos que no se clasificaron correctamente.")

# 🔚 Se cierra el cursor y la conexión a la base de datos
cursor.close()
connection.close()
