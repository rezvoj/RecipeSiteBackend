from os import environ
from pathlib import Path


# NON-CONFIGURABLE

BASE_DIR = Path(__file__).resolve().parent.parent
WSGI_APPLICATION = 'recipeAPI.wsgi.application'
ROOT_URLCONF = 'recipeAPI.urls'

SECRET_KEY = environ.get('APP_SECRET_KEY', 'DEFAULT_UNSECURE_SECRET_KEY')
APP_ADMIN_CODE = environ.get('APP_ADMIN_CODE', 'DEFAULT_UNSECURE_ADMIN_CODE')

USE_I18N = False
USE_TZ = False
TIME_ZONE = None

INSTALLED_APPS = [
    'recipeAPIapp',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'recipeAPIapp.utils.exception.handler',
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# CONFIGURABLE

DEBUG = False
ALLOWED_HOSTS = ['*']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'database/db.sqlite3',
    }
}

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media/'

LOGGING = {
    'version': 1,
    'loggers': {
        'PIL': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = environ.get('APP_EMAIL_HOST')
EMAIL_PORT = environ.get('APP_EMAIL_PORT')
EMAIL_HOST_USER = environ.get('APP_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = environ.get('APP_EMAIL_HOST_PASSWORD')
