import os
import csv

directorio_triadas = os.path.join(os.path.dirname(__file__), 'triadas_por_forma')
archivo_salida = os.path.join(os.path.dirname(__file__), 'todas_las_triadas.csv')

triadas_totales = []

for nombre_archivo in sorted(os.listdir(directorio_triadas)):
    if not nombre_archivo.endswith('.csv'):
        continue
    ruta_archivo = os.path.join(directorio_triadas, nombre_archivo)
    with open(ruta_archivo, 'r') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            triadas_totales.append([
                fila['par_1'],
                fila['par_2'],
                fila['par_3'],
                fila['forma']
            ])

# Guardar archivo combinado
with open(archivo_salida, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['par_1', 'par_2', 'par_3', 'forma'])
    writer.writerows(triadas_totales)

print(f"✅ Total triadas combinadas: {len(triadas_totales)}")
print(f"📄 Archivo generado: {archivo_salida}")
