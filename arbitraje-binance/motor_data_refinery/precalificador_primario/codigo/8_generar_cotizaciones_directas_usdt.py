import os
import pymysql
import ccxt
import csv
from decimal import Decimal, getcontext

# Máxima precisión decimal
getcontext().prec = 50

# Configuración de conexión (con valores por defecto)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "arbitraje_kraken"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# Conexión a la base
connection = pymysql.connect(**DB_CONFIG)
cursor = connection.cursor()

# Leer todos los symbols de cotizador_directo
cursor.execute("SELECT symbol FROM cotizador_directo")
symbols = [row['symbol'] for row in cursor.fetchall()]

# Usamos Kraken
exchange = ccxt.kraken()

# Lista para almacenar los datos de cotización
cotizaciones = []

for symbol in symbols:
    try:
        ticker = exchange.fetch_ticker(symbol)
        precio = Decimal(str(ticker['last']))
        base, quote = symbol.split('/')

        cotizaciones.append({
            'symbol': symbol,
            'base': base,
            'quote': quote,
            '1_base_equivale_usdt': precio,
            '1_usdt_equivale_base': Decimal('1') / precio if precio != 0 else None
        })
    except Exception as e:
        print(f"⚠️ Error con {symbol}: {e}")

# Crear tabla SQL si no existe
cursor.execute("DROP TABLE IF EXISTS cotizaciones_usdt")
cursor.execute("""
    CREATE TABLE cotizaciones_usdt (
        symbol VARCHAR(50),
        base VARCHAR(20),
        quote VARCHAR(20),
        1_base_equivale_usdt DECIMAL(36,18),
        1_usdt_equivale_base DECIMAL(36,18)
    )
""")

# Insertar datos en SQL
cursor.executemany("""
    INSERT INTO cotizaciones_usdt (
        symbol, base, quote, 1_base_equivale_usdt, 1_usdt_equivale_base
    ) VALUES (%s, %s, %s, %s, %s)
""", [
    (
        row['symbol'],
        row['base'],
        row['quote'],
        str(row['1_base_equivale_usdt']),
        str(row['1_usdt_equivale_base']) if row['1_usdt_equivale_base'] else None
    ) for row in cotizaciones
])

connection.commit()

# Crear carpeta de salida organizada
output_folder = os.path.join("codigo", "datos", "cotizaciones_directas_usdt")
os.makedirs(output_folder, exist_ok=True)

# ----------------------------------------
# 1. CSV completo
# ----------------------------------------
csv_path = os.path.join(output_folder, "1_a_cotizaciones_usdt.csv")
with open(csv_path, mode="w", newline='') as file:
    writer = csv.DictWriter(file, fieldnames=[
        'symbol', 'base', 'quote', '1_base_equivale_usdt', '1_usdt_equivale_base'
    ])
    writer.writeheader()
    for row in cotizaciones:
        writer.writerow({
            'symbol': row['symbol'],
            'base': row['base'],
            'quote': row['quote'],
            '1_base_equivale_usdt': str(row['1_base_equivale_usdt']),
            '1_usdt_equivale_base': str(row['1_usdt_equivale_base']) if row['1_usdt_equivale_base'] else ''
        })

# ----------------------------------------
# 2. CSV plano {base: 1_usdt_equivale_base}
# ----------------------------------------
diccionario_base_a_usdt = {
    row['base']: str(row['1_usdt_equivale_base'])
    for row in cotizaciones if row['1_usdt_equivale_base']
}

csv_base_path = os.path.join(output_folder, "2_a_usdt_equivale_base.csv")
with open(csv_base_path, mode="w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['base', '1_usdt_equivale_base'])
    for base, valor in diccionario_base_a_usdt.items():
        writer.writerow([base, valor])

# ----------------------------------------
# 3. Diccionario Python usable con Decimal
# ----------------------------------------
py_dict_path = os.path.join(output_folder, "3_a_cotizador_directo_usdt_equivale_base.py")
with open(py_dict_path, "w") as f:
    f.write("# Diccionario: 1 USDT equivale a cuántas unidades de cada moneda base\n")
    f.write("from decimal import Decimal\n\n")
    f.write("cotizador_usdt_equivale_base = {\n")
    for base, valor in diccionario_base_a_usdt.items():
        f.write(f"    '{base}': Decimal('{valor}'),\n")
    f.write("}\n")

# ----------------------------------------
# Cierre limpio
# ----------------------------------------
cursor.close()
connection.close()

print("✅ Archivos generados en:")
print(f"   📁 {output_folder}")
print(f"   ├── 1_a_cotizaciones_usdt.csv")
print(f"   ├── 2_a_usdt_equivale_base.csv")
print(f"   └── 3_a_cotizador_directo_usdt_equivale_base.py")
