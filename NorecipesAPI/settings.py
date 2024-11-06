from os import environ
from pathlib import Path
import urllib.parse
import json as _json


# NON-CONFIGURABLE

BASE_DIR = Path(__file__).resolve().parent.parent
WSGI_APPLICATION = 'NorecipesAPI.wsgi.application'
ROOT_URLCONF = 'NorecipesAPI.urls'

SECRET_KEY = environ.get('APP_SECRET_KEY', 'DEFAULT_UNSECURE_SECRET_KEY')
APP_ADMIN_CODE = environ.get('APP_ADMIN_CODE', 'DEFAULT_UNSECURE_ADMIN_CODE')

USE_I18N = False
USE_TZ = False
TIME_ZONE = 'UTC'

INSTALLED_APPS = [
    'NorecipesAPIapp',
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
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'NorecipesAPIapp.utils.security.Authentication'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'NorecipesAPIapp.utils.exception.handler',
    # Reject ISO strings with Z or offset suffix to enforce naive-UTC convention.
    'DATETIME_INPUT_FORMATS': [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
    ],
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# CONFIGURABLE
DEBUG = environ.get('APP_DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = environ.get('APP_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Database: Postgres in production via DATABASE_URL, SQLite fallback for local dev and tests.
if environ.get('DATABASE_URL'):
    _url = urllib.parse.urlparse(environ['DATABASE_URL'])
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _url.path[1:],
            'USER': _url.username,
            'PASSWORD': _url.password,
            'HOST': _url.hostname,
            'PORT': _url.port or 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'database/db.sqlite3',
        }
    }

# File storage: local filesystem by default, S3-compatible backend when APP_USE_S3 is enabled.
if environ.get('APP_USE_S3', 'False').lower() == 'true':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3.S3Storage'
    AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = environ.get('AWS_S3_ENDPOINT_URL') or None
    AWS_S3_REGION_NAME = environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_FILE_OVERWRITE = False
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = BASE_DIR / 'media/'

# Logging handler is pluggable: APP_LOG_HANDLER is the dotted path to any logging.Handler
# subclass, APP_LOG_HANDLER_OPTIONS is a JSON dict of constructor kwargs.
import json as _json

_handler_config = {
    'class': environ.get('APP_LOG_HANDLER', 'logging.StreamHandler'),
    **_json.loads(environ.get('APP_LOG_HANDLER_OPTIONS', '{}')),
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        # Pillow emits a lot of debug noise on image loads; keep it at ERROR.
        'PIL': {
            'handlers': ['app'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'handlers': {
        'app': _handler_config,
    },
    'root': {
        'handlers': ['app'],
        'level': environ.get('APP_LOG_LEVEL', 'INFO'),
    },
}

# Email: SMTP for real delivery, console backend (writes to stdout) for local dev.
if environ.get('APP_EMAIL_BACKEND', 'console').lower() == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_USE_TLS = True
    EMAIL_HOST = environ.get('APP_EMAIL_HOST')
    EMAIL_PORT = environ.get('APP_EMAIL_PORT')
    EMAIL_HOST_USER = environ.get('APP_EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = environ.get('APP_EMAIL_HOST_PASSWORD')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    