import csv
import os
from collections import defaultdict

# Configuración
archivo_pares = os.path.join(os.path.dirname(__file__), 'absorcion_filtrada.csv')
directorio_salida = os.path.join(os.path.dirname(__file__), 'triadas_por_forma')
os.makedirs(directorio_salida, exist_ok=True)

# Cargar pares operables
with open(archivo_pares, 'r') as f:
    reader = csv.DictReader(f)
    datos = list(reader)

# Indexar por base y quote
por_base = defaultdict(list)
por_quote = defaultdict(list)

for fila in datos:
    por_base[fila['base']].append(fila)
    por_quote[fila['quote']].append(fila)

# Helper robusto para evitar KeyError
def buscar_pares(origen, modo_compra):
    """Retorna lista de filas donde se pueda ir desde `origen`"""
    return por_quote.get(origen, []) if modo_compra else por_base.get(origen, [])

# Probar las 8 combinaciones (000 a 111)
for forma in range(8):
    b1 = bool((forma >> 2) & 1)  # dirección primer salto
    b2 = bool((forma >> 1) & 1)  # dirección segundo salto
    b3 = bool((forma >> 0) & 1)  # dirección tercer salto

    nombre_forma = f"forma_{forma+1}_{int(b1)}{int(b2)}{int(b3)}"
    salida = os.path.join(directorio_salida, f"{nombre_forma}.csv")

    triadas = []

    for fila1 in buscar_pares('USDT', b1):
        moneda_1 = fila1['base'] if b1 else fila1['quote']

        for fila2 in buscar_pares(moneda_1, b2):
            moneda_2 = fila2['base'] if b2 else fila2['quote']

            for fila3 in buscar_pares(moneda_2, b3):
                moneda_3 = fila3['base'] if b3 else fila3['quote']

                if moneda_3 == 'USDT':
                    triadas.append([
                        fila1['symbol'],
                        fila2['symbol'],
                        fila3['symbol'],
                        f"{nombre_forma}"
                    ])

    # Guardar CSV aunque esté vacío
    with open(salida, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['par_1', 'par_2', 'par_3', 'forma'])
        writer.writerows(triadas)

    print(f"✅ {nombre_forma}: {len(triadas)} triadas generadas → {salida}")
