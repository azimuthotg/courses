import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-insecure-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]

# IIS Subpath Deployment (Critical)
FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME', '')
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_tailwind',
    'lms',
]

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

ROOT_URLCONF = 'config.urls'
AUTH_USER_MODEL = 'lms.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'lms' / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'lms_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Static & Media
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
FILE_UPLOAD_PERMISSIONS = None

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication
NPU_STUDENT_AUTH_ENABLED = os.getenv('NPU_STUDENT_AUTH_ENABLED', 'True').lower() in ('true', '1', 'yes')
NPU_STUDENT_AUTH_URL = os.getenv(
    'NPU_STUDENT_AUTH_URL',
    'https://api.npu.ac.th/v2/ldap/auth_and_get_student/',
)
NPU_STUDENT_AUTH_TOKEN = os.getenv('NPU_STUDENT_AUTH_TOKEN', '')
NPU_STUDENT_AUTH_TIMEOUT = int(os.getenv('NPU_STUDENT_AUTH_TIMEOUT', '10'))
NPU_STUDENT_CODE_LENGTH = int(os.getenv('NPU_STUDENT_CODE_LENGTH', '12'))

AUTHENTICATION_BACKENDS = [
    'lms.auth_backends.NPUStudentAPIBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# LDAP Authentication — enable by setting LDAP_ENABLED=True in .env
if os.getenv('LDAP_ENABLED', 'False').lower() in ('true', '1', 'yes'):
    try:
        import ldap
        from django_auth_ldap.config import LDAPSearch

        AUTH_LDAP_SERVER_URI = os.getenv('LDAP_SERVER_URI', 'ldap://ad.npu.ac.th')
        AUTH_LDAP_BIND_DN = os.getenv('LDAP_BIND_DN', '')
        AUTH_LDAP_BIND_PASSWORD = os.getenv('LDAP_BIND_PASSWORD', '')
        AUTH_LDAP_USER_SEARCH = LDAPSearch(
            os.getenv('LDAP_USER_BASE_DN', 'DC=npu,DC=ac,DC=th'),
            ldap.SCOPE_SUBTREE,
            '(sAMAccountName=%(user)s)',
        )
        AUTH_LDAP_USER_ATTR_MAP = {
            'first_name': 'givenName',
            'last_name': 'sn',
            'email': 'mail',
        }
        AUTH_LDAP_ALWAYS_UPDATE_USER = True

        AUTHENTICATION_BACKENDS = [
            'lms.auth_backends.NPUStudentAPIBackend',
            'django_auth_ldap.backend.LDAPBackend',
            'django.contrib.auth.backends.ModelBackend',
        ]
    except ImportError:
        pass

# crispy-forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Internationalization
LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
