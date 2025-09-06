import os
import shutil

ARCHIVOS = [
    'todas_las_triadas.csv',
    'pares_involucrados.csv',
]
CARPETA = 'triadas_por_forma'
DESTINO = '/app/salida'  # no borrar esta carpeta directamente

# 🧹 Limpiar contenido previo de salida (sin borrar /app/salida)
if not os.path.exists(DESTINO):
    os.makedirs(DESTINO)

for nombre in os.listdir(DESTINO):
    ruta = os.path.join(DESTINO, nombre)
    try:
        if os.path.isfile(ruta) or os.path.islink(ruta):
            os.unlink(ruta)
        elif os.path.isdir(ruta):
            shutil.rmtree(ruta)
    except Exception as e:
        print(f'⚠️ Error al borrar {ruta}: {e}')
print(f'🧼 Contenido de {DESTINO} limpiado')

# 📄 Copiar archivos individuales
for archivo in ARCHIVOS:
    origen = os.path.join('modulo_absorcion', archivo)
    destino_archivo = os.path.join(DESTINO, archivo)
    if os.path.exists(origen):
        shutil.copy2(origen, destino_archivo)
        print(f'✅ Archivo copiado: {archivo}')
    else:
        print(f'❌ Archivo NO encontrado: {archivo}')

# 📂 Copiar carpeta completa
origen_carpeta = os.path.join('modulo_absorcion', CARPETA)
destino_carpeta = os.path.join(DESTINO, CARPETA)

if os.path.exists(origen_carpeta):
    shutil.copytree(origen_carpeta, destino_carpeta)
    print(f'✅ Carpeta copiada: {CARPETA}')
else:
    print(f'❌ Carpeta NO encontrada: {CARPETA}')
