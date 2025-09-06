"""
Valida que los datos estructurales cargados para Kraken estén consistentes y completos
comparando la base de datos contra los datos reales de CCXT (`load_markets()`).
Aplica tolerancia para evitar falsos positivos en diferencias de formato numérico.
No asume jerarquía: compara clave-valor de forma plana y recursiva.
"""

import os
import pymysql
import ccxt
# from dotenv import load_dotenv  # Opcional para cargar variables de entorno desde .env

# ---------------------------------------------------------------------------
# 1. Cargar configuración y entorno (variables de entorno para DB)
# ---------------------------------------------------------------------------

# load_dotenv()  # Comentado: se puede activar si se necesita leer desde .env

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

TOLERANCIA = 1e-8  # Diferencia máxima aceptable para valores numéricos
EXCHANGE_ID = "kraken"  # Exchange objetivo a validar

# ---------------------------------------------------------------------------
# 2. Conexión y helpers SQL
# ---------------------------------------------------------------------------

def conectar_db():
    """Conecta a la base de datos usando la configuración del entorno."""
    return pymysql.connect(**DB_CONFIG)

def tabla_existe(conn, tabla):
    """Verifica si una tabla específica existe en la base de datos."""
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", (tabla,))
        return cursor.fetchone() is not None

def obtener_tablas_relacionadas(conn, exchange_id):
    """
    Devuelve todas las tablas de la base de datos que empiezan con
    <exchange>_sym_ — por ejemplo: kraken_sym_symbols, kraken_sym_precision, etc.
    """
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        todas = [fila[f'Tables_in_{DB_CONFIG["database"]}'] for fila in cursor.fetchall()]
        return [t for t in todas if t.startswith(f"{exchange_id}_sym_")]

def obtener_datos_por_symbol_id(conn, tablas):
    """
    Carga todas las filas de todas las tablas relacionales del exchange,
    agrupándolas por `symbol_id` y combinando los campos para ese símbolo.
    """
    datos = {}
    for tabla in tablas:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM `{tabla}`")
            filas = cursor.fetchall()
            for fila in filas:
                sym_id = fila.get("symbol_id")
                if not sym_id:
                    continue
                if sym_id not in datos:
                    datos[sym_id] = {}
                # Fusiona los campos del símbolo, salvo el propio symbol_id
                datos[sym_id].update({k: v for k, v in fila.items() if k != "symbol_id"})
    return datos

# ---------------------------------------------------------------------------
# 3. Comparación recursiva y validación campo por campo
# ---------------------------------------------------------------------------

def buscar_clave_recursiva(diccionario, clave):
    """Busca recursivamente una clave en cualquier parte del diccionario (incluso anidado)."""
    if isinstance(diccionario, dict):
        if clave in diccionario:
            return diccionario[clave]
        for v in diccionario.values():
            resultado = buscar_clave_recursiva(v, clave)
            if resultado is not None:
                return resultado
    elif isinstance(diccionario, list):
        for item in diccionario:
            resultado = buscar_clave_recursiva(item, clave)
            if resultado is not None:
                return resultado
    return None

def comparar_valores(campo, valor_db, valor_ccxt):
    """
    Compara dos valores para un campo dado:
    - Si ambos son numéricos, compara con tolerancia.
    - Si son strings u otros, compara exactitud.
    Devuelve mensaje de error si hay diferencias, o None si están OK.
    """
    if valor_ccxt is None:
        return f"⚠️ {campo} no encontrado en CCXT"
    if valor_db is None:
        return f"⚠️ {campo} está vacío en DB"
    try:
        db_float = float(valor_db)
        ccxt_float = float(valor_ccxt)
        if abs(db_float - ccxt_float) > TOLERANCIA:
            return f"❌ {campo} difiere: DB={valor_db} | CCXT={valor_ccxt}"
    except:
        if str(valor_db) != str(valor_ccxt):
            return f"❌ {campo} difiere: DB='{valor_db}' | CCXT='{valor_ccxt}'"
    return None

def validar_symbol(exchange, symbol_id, symbol, datos_dict, errores):
    """
    Valida un símbolo comparando cada campo almacenado en la DB contra el
    dato real en tiempo real devuelto por `exchange.markets[symbol]`.
    Agrega errores al listado global si hay inconsistencias.
    """
    try:
        market = exchange.markets[symbol]
    except KeyError:
        errores.append(f"❌ {symbol_id} no existe en CCXT")
        return

    if not isinstance(datos_dict, dict):
        errores.append(f"⚠️ {symbol_id} tiene datos mal estructurados en DB (esperado dict, recibido {type(datos_dict)})")
        return

    for campo, valor_db in datos_dict.items():
        valor_ccxt = buscar_clave_recursiva(market, campo)
        resultado = comparar_valores(campo, valor_db, valor_ccxt)
        if resultado:
            errores.append(f"{symbol_id} → {resultado}")

# ---------------------------------------------------------------------------
# 4. Ejecución principal
# ---------------------------------------------------------------------------

def main():
    try:
        exchange = getattr(ccxt, EXCHANGE_ID)()
        exchange.load_markets()
    except Exception as e:
        print(f"❌ No se pudo instanciar exchange CCXT: {e}")
        return

    conn = conectar_db()
    tablas = obtener_tablas_relacionadas(conn, EXCHANGE_ID)
    if not tablas:
        print(f"❌ No se encontraron tablas {EXCHANGE_ID}_sym_*")
        return

    datos_por_symbol = obtener_datos_por_symbol_id(conn, tablas)
    total = len(datos_por_symbol)

    print(f"🔎 Validando {total} símbolos en '{EXCHANGE_ID}'…")
    errores = []

    for i, (symbol_id, datos) in enumerate(datos_por_symbol.items(), 1):
        if not isinstance(datos, dict):
            errores.append(f"⚠️ {symbol_id} tiene datos corruptos en DB")
            continue

        symbol = datos.get("symbol")
        if not symbol:
            errores.append(f"⚠️ {symbol_id} no tiene campo 'symbol'")
            continue

        validar_symbol(exchange, symbol_id, symbol, datos, errores)

        if i % 5 == 0:
            print(f"→ Validados {i} símbolos...")

    conn.close()

    # Mostrar resultado final
    if errores:
        print("\n❌ Inconsistencias encontradas:")
        for err in errores:
            print("-", err)
    else:
        print(f"\n✔️ Todos los {total} símbolos fueron validados correctamente contra CCXT.")

    print("\n🎯 Validación completa.")

if __name__ == "__main__":
    main()
