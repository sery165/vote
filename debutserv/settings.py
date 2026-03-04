from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-temp-key'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',   # ← ok
    'django.contrib.staticfiles', # ← ok

    'rest_framework',
    'corsheaders',
    'serveurcei',
    'vote',

    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8001",
]

# Dans debutserv/settings.py

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny', # Autorise l'accès sans login pour tes tests
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

ROOT_URLCONF = 'debutserv.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # On dit à Django de chercher spécifiquement dans le dossier templates de serveurcei
        'DIRS': [BASE_DIR / 'serveurcei' / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', # Ajoute celui-ci pour aider au debug
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'debutserv.wsgi.application'

# debutserv/settings.py

# debutserv/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # On change pour MySQL/MariaDB
        'NAME': 'serveur',                   # Le nom de ta base vue dans MariaDB
        'USER': 'root',                      # Ton utilisateur MariaDB (souvent root)
        'PASSWORD': 'MOREL1234',      # Ton mot de passe MariaDB
        'HOST': '127.0.0.1',
        'PORT': '3306',                      # Port par défaut de MariaDB/MySQL
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# settings.py
SECURE_SSL_REDIRECT = False  # Pour HTTPS en production
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False