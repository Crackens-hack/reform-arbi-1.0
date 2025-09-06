import os
import csv

archivo_entrada = os.path.join(os.path.dirname(__file__), 'todas_las_triadas.csv')
archivo_salida = os.path.join(os.path.dirname(__file__), 'pares_involucrados.csv')

# Leer triadas
triadas = []
with open(archivo_entrada, 'r') as f:
    reader = csv.DictReader(f)
    for fila in reader:
        triadas.extend([fila['par_1'], fila['par_2'], fila['par_3']])

# Eliminar duplicados y ordenar
pares_unicos = sorted(set(triadas))

# Guardar archivo
with open(archivo_salida, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['symbol'])
    for par in pares_unicos:
        writer.writerow([par])

print(f"✅ Total pares únicos involucrados: {len(pares_unicos)}")
print(f"📄 Archivo generado: {archivo_salida}")
