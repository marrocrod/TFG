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

media_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')

def delete_media_files():
    if os.path.exists(media_folder):
        # Recorre todos los archivos y carpetas en "media"
        for filename in os.listdir(media_folder):
            file_path = os.path.join(media_folder, filename)
            try:
                # Si es un archivo, lo elimina
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f'Archivo {file_path} eliminado.')
                # Si es una carpeta, la elimina junto con su contenido
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f'Carpeta {file_path} eliminada.')
            except Exception as e:
                print(f'Error al eliminar {file_path}. Razón: {e}')
    else:
        print('La carpeta media no existe.')

if __name__ == '__main__':
    delete_media_files()