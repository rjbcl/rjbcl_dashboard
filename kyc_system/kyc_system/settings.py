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

ALLOWED_HOSTS = ['10.91.1.29','127.0.0.1']


# APPLICATIONS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # KYC Application
    'kycform',
]


# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'kycform', 'static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# -----------------------------------------------------------
# ✅ MEDIA FILE SETTINGS (REQUIRED for File Upload Preview)
# -----------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# -----------------------------------------------------------


API_BACKEND_TOKEN = "super-secret-backend-token-123456"
FASTAPI_BASE_URL = "http://127.0.0.1:9000"

# ------------------------------
# FASTAPI INTEGRATION SETTINGS
# ------------------------------
API_BASE_URL = config("API_BASE_URL", default="http://127.0.0.1:9000")
API_TOKEN = config("API_TOKEN", default="super-secret-backend-token-123456")
