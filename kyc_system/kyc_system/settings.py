"""
Django settings for kyc_system project.
"""

from pathlib import Path
import os
from decouple import Config, RepositoryEnv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
ENV_PATH = os.path.join(BASE_DIR, ".env")
config = Config(RepositoryEnv(ENV_PATH))


# SECURITY
SECRET_KEY = config("SECRET_KEY", default="unsafe-secret-key")
DEBUG = config("DEBUG", default=True, cast=bool)
# DEBUG = False

ALLOWED_HOSTS = ['*']


# APPLICATIONS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'react_frontend',
    # KYC Application
    'kycform',
]

# CSRF Settings
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # Important: Must be False so JavaScript can read it
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False  # Set to True only in production with HTTPS
CSRF_USE_SESSIONS = False
CSRF_COOKIE_PATH = '/'

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

# Session Configuration for React Integration
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_DOMAIN = None  # Important: allows localhost subdomains
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_PATH = '/'

# Important: This allows the session to work across localhost:3000 and localhost:8000
SESSION_COOKIE_SAMESITE = None  # Change from 'Lax' to None for cross-origin
SESSION_COOKIE_SECURE = False   # Must be False for localhost (True for production HTTPS)

# CSRF Configuration
CSRF_COOKIE_SAMESITE = None  # Change from 'Lax' to None
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}




# MIDDLEWARE
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kyc_system.urls'


# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'kycform' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kyc_system.wsgi.application'


# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config("PGNAME"),
        'USER': config("PGUSER"),
        'PASSWORD': config("PGPASSWORD"),
        'HOST': config("PGHOST"),
        'PORT': config("PGPORT"),
        'OPTIONS': {
            'sslmode': config("PGSSL", default="require"),
        }
    }
}


# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True


# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'kycform' / 'static',
]

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# -----------------------------------------------------------
# ✅ MEDIA FILE SETTINGS (REQUIRED for File Upload Preview)
# -----------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# -----------------------------------------------------------


API_BACKEND_TOKEN = "super-secret-backend-token-123456"
FASTAPI_BASE_URL = "http://127.0.0.1:9000"

# ------------------------------
# FASTAPI INTEGRATION SETTINGS
# ------------------------------
API_BASE_URL = config("API_BASE_URL", default="http://127.0.0.1:9000")
API_TOKEN = config("API_TOKEN", default="super-secret-backend-token-123456")

# SESSION SETTINGS
SESSION_COOKIE_AGE = 20 * 60  # 20 minutes
SESSION_SAVE_EVERY_REQUEST = True
