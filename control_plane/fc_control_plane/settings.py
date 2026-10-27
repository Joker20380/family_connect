import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
if os.environ.get('CONTROL_PLANE_MODE') != 'synthetic':
    raise ImproperlyConfigured('CONTROL-PLANE-0 only permits synthetic mode')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if len(SECRET_KEY) < 48 or SECRET_KEY.startswith('REPLACE_'):
    raise ImproperlyConfigured('Provide a private random DJANGO_SECRET_KEY of at least 48 characters')
database_password = os.environ.get('POSTGRES_PASSWORD', '')
if len(database_password) < 20 or database_password.startswith('REPLACE_'):
    raise ImproperlyConfigured('Provide a private random POSTGRES_PASSWORD of at least 20 characters')
database_host = os.environ.get('POSTGRES_HOST', '127.0.0.1')
if database_host not in ('postgres', '127.0.0.1', 'localhost'):
    raise ImproperlyConfigured('Only local PostgreSQL is permitted')
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'apps.console.apps.ConsoleConfig',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fc_control_plane.middleware.LocalConsoleHeaders',
]
ROOT_URLCONF = 'fc_control_plane.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True, 'OPTIONS': {'context_processors': [
        'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'fc_control_plane.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql', 'NAME': 'fc_control_plane', 'USER': 'fc_control_plane',
    'PASSWORD': database_password, 'HOST': database_host, 'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    'CONN_MAX_AGE': 0, 'OPTIONS': {'connect_timeout': 5},
}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 14}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / '.local' / 'static'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
LOGIN_URL = '/admin/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8765', 'http://localhost:8765']
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 32768
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40
