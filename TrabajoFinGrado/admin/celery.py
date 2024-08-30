from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración predeterminado de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrabajoFinGrado.settings')

app = Celery('TrabajoFinGrado')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar las tareas definidas en los módulos de la aplicación django
app.autodiscover_tasks()
