"""
Django settings for TrabajoFinGrado project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure--e&+gw%v*k-1v76w%21xlui2u+pkv4y%w+belk^@buy(r!kojx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    'students',
    'teachers',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middleware.SessionTimeoutMiddleware', 

]

ROOT_URLCONF = 'admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'admin.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

BASE_DIR / "main/static",

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#LOGIN
LOGIN_REDIRECT_URL = 'home'  
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

#AUTH USER
AUTH_USER_MODEL = 'main.User'


#API OPENAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")


#SESION

SESSION_COOKIE_AGE = 1800  # 30 minutos en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

#EMAIL

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'  # Este es el host SMTP para Hotmail/Outlook
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'saymplexfp@hotmail.com'  # Reemplaza con tu dirección de correo de Hotmail
EMAIL_HOST_PASSWORD = 'Y&P3WMaiK&7q'  # Reemplaza con tu contraseña correcta
DEFAULT_FROM_EMAIL = 'saymplexfp@hotmail.com'  # Puede ser el mismo que EMAIL_HOST_USER


#CELERY
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Configuración del broker de Celery, puede ser Redis o RabbitMQ
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'delete_unactivated_users_every_hour': {
        'task': 'main.tasks.delete_unactivated_users',
        'schedule': crontab(minute=0, hour='*/1'),  # Cada hora
    },
}

