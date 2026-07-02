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
    
    # KYC Application
    'kycform',
]


# MIDDLEWARE
MIDDLEWARE = [
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
    # KYC DATABASE (UNCHANGED)
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PGNAME'),
        'USER': config('PGUSER'),
        'PASSWORD': config('PGPASSWORD'),
        'HOST': config('PGHOST'),
        'PORT': config('PGPORT'),
        'OPTIONS': {
            'sslmode': config('PGSSL', default='require'),
        }
    },

    # CORE INSURANCE DATABASE (SQL SERVER – READ ONLY)
    'sqlserver': {
        'ENGINE': 'mssql',
        'NAME': config('MSSQL_NAME'),
        'USER': config('MSSQL_USER'),
        'PASSWORD': config('MSSQL_PASSWORD'),
        'HOST': config('MSSQL_HOST'),
        'PORT': config('MSSQL_PORT', default='1433'),
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'extra_params': 'Encrypt=yes;TrustServerCertificate=yes;',
        },
    }

}


# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}




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


# ============================================================
# EXTERNAL BACKEND SERVICES (SEPARATED BY DOMAIN)
# ============================================================

# ---- CORE INSURANCE API (AGENT / BUSINESS DATA) ----
CORE_API_BASE_URL = config(
    "CORE_API_BASE_URL",
    default="http://127.0.0.1:8100"
)
CORE_API_TOKEN = config(
    "CORE_API_TOKEN",
    default="super-secret-core-token"
)

# ---- KYC FASTAPI SERVICE (POLICY / PERSON KYC) ----
KYC_API_BASE_URL = config(
    "KYC_API_BASE_URL",
    default="http://127.0.0.1:9000"
)
KYC_API_TOKEN = config(
    "KYC_API_TOKEN",
    default="super-secret-kyc-token"
)

# ---- SMS GATEWAY (KYC VERIFICATION NOTIFICATIONS) ----
SMS_GATEWAY_URL = config("SMS_GATEWAY_URL", default="")
SMS_GATEWAY_TOKEN = config("SMS_GATEWAY_TOKEN", default="")
SMS_GATEWAY_TIMEOUT = config("SMS_GATEWAY_TIMEOUT", default=15, cast=int)

# ---- FASTAPI OTP/SMS SERVICE ----
# Point this to the api_service app, e.g. http://127.0.0.1:8001
API_SERVICE_BASE_URL = config("API_SERVICE_BASE_URL", default="http://127.0.0.1:8001")

# ---- POLICY SERVICE URLS (LOCAL DASHBOARD CONFIG) ----
PREMIUM_PAYMENT_URL = config(
    "PREMIUM_PAYMENT_URL",
    default="https://rbs.gov.np/premium-payment"
)
LOAN_REPAYMENT_URL = config(
    "LOAN_REPAYMENT_URL",
    default="https://lims.rbs.gov.np:2028/Transaction/LoanRepaymentSearch/loan-payment"
)
FOREIGN_POLICY_URL = config(
    "FOREIGN_POLICY_URL",
    default="https://rbs.gov.np/foreign-policy"
)

RECAPTCHA_SITE_KEY = config(
    "RECAPTCHA_SITE_KEY",
    default="6LdykNEsAAAAAJZkPHkyaJcoCWtrCg65WJlAG511",
)
RECAPTCHA_SECRET_KEY = config(
    "RECAPTCHA_SECRET_KEY",
    default="",
)


# SESSION SETTINGS
SESSION_COOKIE_AGE = 20 * 60  # 20 minutes
SESSION_SAVE_EVERY_REQUEST = True
