import os
import shutil

# Define las rutas que deseas limpiar
directories = [
    'main/__pycache__/',
    'main/migrations/__pycache__/',
    'students/__pycache__/',
    'students/migrations/__pycache__/',
    'teachers/__pycache__/',
    'teachers/migrations/__pycache__/'
]

# Eliminar carpetas __pycache__
for dir_path in directories:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
        print(f'Eliminado: {dir_path}')

# Eliminar archivos de migraciones que no sean __init__.py
migration_dirs = [
    'main/migrations/',
    'students/migrations/',
    'teachers/migrations/'
]
for dir_path in migration_dirs:
    if os.path.exists(dir_path):
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if filename != '__init__.py' and os.path.isfile(file_path):
                os.remove(file_path)
                print(f'Eliminado: {file_path}')

print('Limpieza completada')
