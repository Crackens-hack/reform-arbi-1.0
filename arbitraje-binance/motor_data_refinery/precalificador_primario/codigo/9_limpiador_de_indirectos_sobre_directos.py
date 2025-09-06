import os
import pymysql
import ccxt
import csv
from decimal import Decimal, getcontext, InvalidOperation

# Configura una altísima precisión decimal para operaciones financieras críticas
getcontext().prec = 50

# Configuración de conexión a la base de datos usando variables de entorno, con valores por defecto
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "arbitraje_kraken"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# Establece conexión a la base de datos
connection = pymysql.connect(**DB_CONFIG)
cursor = connection.cursor()

# Consulta todas las bases del cotizador directo (monedas que cotizan directamente contra USDT, por ejemplo)
cursor.execute("SELECT base FROM cotizador_directo")
bases_directas = set(row['base'] for row in cursor.fetchall())

# Trae todos los pares indirectos (aquellos que no cotizan directamente con USDT)
cursor.execute("SELECT symbol, base, quote FROM cotizador_indirecto")
pares_indirectos = cursor.fetchall()

# Instancia de la API de Kraken a través de CCXT
exchange = ccxt.kraken()

# Inicializa listas para almacenar pares filtrados y descartados
filtrados = []
descartados = []

# Itera sobre todos los pares indirectos
for row in pares_indirectos:
    base, quote = row['base'], row['quote']
    match_info = []

    # Indica si la base cotiza contra USDT
    if base in bases_directas:
        match_info.append(f"base:{base}")
    else:
        match_info.append("base:NONE")

    # Indica si la quote cotiza contra USDT
    if quote in bases_directas:
        match_info.append(f"quote:{quote}")
    else:
        match_info.append("quote:NONE")

    # Anexa la info de cotización con respecto al cotizador directo
    row['cotiza_vs_directo'] = "; ".join(match_info)

    # Si al menos una de las dos monedas cotiza contra USDT, se intenta obtener su precio
    if base in bases_directas or quote in bases_directas:
        try:
            ticker = exchange.fetch_ticker(row['symbol'])  # Consulta el precio de mercado
            precio = Decimal(str(ticker['last']))  # Precio del último trade como Decimal
            row['1_base_equivale_x_quote'] = precio  # Cuánto vale 1 unidad de base en quote
            row['1_quote_equivale_x_base'] = Decimal('1') / precio if precio != 0 else None  # Inverso
        except (Exception, InvalidOperation):
            # Si algo falla (precio inválido, error de red, etc), se registran como None
            row['1_base_equivale_x_quote'] = None
            row['1_quote_equivale_x_base'] = None
        filtrados.append(row)  # Se agrega a la lista de pares filtrados
    else:
        # Si ninguna cotiza contra USDT, se descarta el par
        row['1_base_equivale_x_quote'] = None
        row['1_quote_equivale_x_base'] = None
        descartados.append(row)

# Elimina la tabla anterior si existe y crea una nueva tabla para pares filtrados con campos DECIMAL
cursor.execute("DROP TABLE IF EXISTS pares_indirectos_filtrados")
cursor.execute("""
    CREATE TABLE pares_indirectos_filtrados (
        symbol VARCHAR(50),
        base VARCHAR(20),
        quote VARCHAR(20),
        cotiza_vs_directo TEXT,
        1_base_equivale_x_quote DECIMAL(50,30),
        1_quote_equivale_x_base DECIMAL(50,30)
    )
""")

# Inserta los pares filtrados en la tabla nueva
cursor.executemany("""
    INSERT INTO pares_indirectos_filtrados (
        symbol, base, quote, cotiza_vs_directo,
        1_base_equivale_x_quote, 1_quote_equivale_x_base
    ) VALUES (%s, %s, %s, %s, %s, %s)
""", [
    (
        r['symbol'],
        r['base'],
        r['quote'],
        r['cotiza_vs_directo'],
        str(r['1_base_equivale_x_quote']) if r['1_base_equivale_x_quote'] else None,
        str(r['1_quote_equivale_x_base']) if r['1_quote_equivale_x_base'] else None
    )
    for r in filtrados
])

# Elimina la tabla anterior si existe y crea una tabla para pares descartados
cursor.execute("DROP TABLE IF EXISTS pares_indirectos_descartados")
cursor.execute("""
    CREATE TABLE pares_indirectos_descartados (
        symbol VARCHAR(50),
        base VARCHAR(20),
        quote VARCHAR(20),
        cotiza_vs_directo TEXT
    )
""")

# Inserta los pares descartados (sin cotización directa posible)
cursor.executemany("""
    INSERT INTO pares_indirectos_descartados (symbol, base, quote, cotiza_vs_directo)
    VALUES (%s, %s, %s, %s)
""", [(r['symbol'], r['base'], r['quote'], r['cotiza_vs_directo']) for r in descartados])

# Define la carpeta de salida para guardar los CSV
output_folder = os.path.join("codigo", "datos", "previo_a_cotizar")
os.makedirs(output_folder, exist_ok=True)

# Función utilitaria para guardar un CSV desde una lista de diccionarios
def guardar_csv(nombre_archivo, datos):
    if not datos:
        print(f"⚠️ No hay datos para guardar en {nombre_archivo}")
        return
    ruta = os.path.join(output_folder, nombre_archivo)
    fieldnames = list(datos[0].keys())  # Usa las claves del primer dict como encabezados
    with open(ruta, mode="w", newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in datos:
            row_copy = row.copy()  # Evita modificar el original
            # Formatea los valores decimales si existen
            if row_copy.get('1_base_equivale_x_quote') is not None:
                row_copy['1_base_equivale_x_quote'] = format(Decimal(row_copy['1_base_equivale_x_quote']), 'f')
            if row_copy.get('1_quote_equivale_x_base') is not None:
                row_copy['1_quote_equivale_x_base'] = format(Decimal(row_copy['1_quote_equivale_x_base']), 'f')
            writer.writerow(row_copy)

# Guarda los pares procesados en CSVs separados
guardar_csv("pares_indirectos_filtrados.csv", filtrados)
guardar_csv("pares_indirectos_descartados.csv", descartados)

# Cierre de la conexión
connection.commit()
cursor.close()
connection.close()

# Mensaje final de éxito
print("✅ Finalizado: precisión quirúrgica absoluta con Decimal(50,30), incluyendo cotiza_vs_directo explícito.")
print(f"📁 Archivos CSV generados en: {output_folder}")
