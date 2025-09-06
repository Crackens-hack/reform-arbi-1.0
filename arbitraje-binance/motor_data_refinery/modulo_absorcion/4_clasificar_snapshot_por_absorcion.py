# archivo: modulo_absorcion/clasificar_snapshot_por_absorcion.py

import csv
import os
import pymysql

# 📁 Rutas de archivos
archivo_entrada = os.path.join(os.path.dirname(__file__), 'snapshot_multi_slippage.csv')
archivo_filtrados = os.path.join(os.path.dirname(__file__), 'absorcion_filtrada.csv')
archivo_descartados = os.path.join(os.path.dirname(__file__), 'absorcion_descartados.csv')

# 🛠️ Conexión a base de datos común
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

# 🔐 Columnas de salida
columnas_salida = [
    'symbol', 'base', 'quote', 'capital_simulado_quote',
    'capital_usdt_equiv_003_slip', 'nivel', 'clasificacion'
]

# 🧮 Leer y procesar snapshot
with open(archivo_entrada, 'r') as f:
    reader = csv.DictReader(f)
    datos = list(reader)

filtrados = []
descartados = []

for fila in datos:
    try:
        symbol = fila['symbol']
        base, quote = symbol.split('/')
        capital_simulado = float(fila['capital_simulado_quote'])
        capital_usdt = float(fila['capital_usdt_equiv_003_slip'])
        nivel = int(fila['niveles_usados_003_slip'])

        if capital_usdt < 10000:
            clasif = 'descartado'
            descartados.append([symbol, base, quote, capital_simulado, capital_usdt, nivel, clasif])
        else:
            if capital_usdt >= 50000:
                clasif = 'optimo'
            elif capital_usdt >= 30000:
                clasif = 'alto'
            elif capital_usdt >= 20000:
                clasif = 'medio'
            else:
                clasif = 'bajo'
            filtrados.append([symbol, base, quote, capital_simulado, capital_usdt, nivel, clasif])
    except Exception as e:
        print(f"⚠️ Error procesando fila: {fila} → {e}")

# 💾 Guardar CSVs
with open(archivo_filtrados, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(columnas_salida)
    writer.writerows(filtrados)

with open(archivo_descartados, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(columnas_salida)
    writer.writerows(descartados)

print("✅ Archivos CSV generados correctamente.")

# 🛢️ Guardar en MariaDB tabla: kraken_pares_operables
try:
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Crear tabla si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kraken_pares_operables (
            symbol VARCHAR(50) PRIMARY KEY,
            base VARCHAR(20),
            quote VARCHAR(20),
            capital_simulado_quote DECIMAL(32,12),
            capital_usdt_equiv_003_slip DECIMAL(32,12),
            niveles_usados_003_slip INT,
            clasificacion VARCHAR(20)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # Insertar o actualizar
    for fila in filtrados:
        cur.execute("""
            INSERT INTO kraken_pares_operables (
                symbol, base, quote, capital_simulado_quote,
                capital_usdt_equiv_003_slip, niveles_usados_003_slip, clasificacion
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                capital_simulado_quote = VALUES(capital_simulado_quote),
                capital_usdt_equiv_003_slip = VALUES(capital_usdt_equiv_003_slip),
                niveles_usados_003_slip = VALUES(niveles_usados_003_slip),
                clasificacion = VALUES(clasificacion)
        """, fila)

    cur.close()
    conn.close()
    print("✅ Datos insertados en MariaDB → `kraken_pares_operables`")

except Exception as e:
    print(f"❌ Error al conectar o insertar en la base de datos: {e}")
