"""
facesyma_project/settings.py
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Güvenlik ───────────────────────────────────────────────────────────────────
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not _SECRET_KEY:
    if DEBUG:
        _SECRET_KEY = 'django-insecure-dev-only-not-for-production'
    else:
        raise RuntimeError('DJANGO_SECRET_KEY environment variable must be set in production.')
SECRET_KEY = _SECRET_KEY

# Production'da ALLOWED_HOSTS env variable ile set edilmeli (örn: 'api.facesyma.com')
_raw_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = _raw_hosts.split(',')

# ── Uygulamalar ────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',  # Must be first for ASGI support
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'channels',  # WebSocket support
    'analysis_api',
    'auth_api',
    'admin_api',
    'gamification',  # Gamification app with WebSocket consumers
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.locale.LocaleMiddleware',  # Disabled: .mo files compiled separately
]

ROOT_URLCONF = 'facesyma_project.urls'
WSGI_APPLICATION = 'facesyma_project.wsgi.application'

# ── Veritabanı (Django ORM kullanılmıyor — sadece MongoDB) ─────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── MongoDB ────────────────────────────────────────────────────────────────────
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb://localhost:27017/facesyma-backend'  # Override with MONGO_URI env var in production
)

# ── JWT ────────────────────────────────────────────────────────────────────────
_JWT_SECRET = os.environ.get('JWT_SECRET', '')
if not _JWT_SECRET:
    if DEBUG:
        _JWT_SECRET = 'dev-jwt-secret-not-for-production'
    else:
        raise RuntimeError('JWT_SECRET environment variable must be set in production.')
JWT_SECRET = _JWT_SECRET

JWT_ACCESS_EXP_HOURS   = int(os.environ.get('JWT_ACCESS_EXP_HOURS', '1'))
JWT_REFRESH_EXP_DAYS   = int(os.environ.get('JWT_REFRESH_EXP_DAYS', '30'))

# ── Admin JWT ──────────────────────────────────────────────────────────────────
_ADMIN_JWT_SECRET = os.environ.get('ADMIN_JWT_SECRET', '')
if not _ADMIN_JWT_SECRET:
    if DEBUG:
        _ADMIN_JWT_SECRET = 'dev-admin-jwt-secret-not-for-production'
    else:
        raise RuntimeError('ADMIN_JWT_SECRET environment variable must be set in production.')
ADMIN_JWT_SECRET = _ADMIN_JWT_SECRET
ADMIN_JWT_EXP_HOURS = int(os.environ.get('ADMIN_JWT_EXP_HOURS', '8'))

# ── Google OAuth ───────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# ── Payment Processing ──────────────────────────────────────────────────────────
# Google Pay ve Apple Pay client-side işlenir — server key gerektirmez.
GOOGLE_PAY_MERCHANT_ID = os.environ.get('GOOGLE_PAY_MERCHANT_ID', '')
APPLE_PAY_MERCHANT_ID  = os.environ.get('APPLE_PAY_MERCHANT_ID', '')
# Vakıfbank Sanal Pos — ileriki versiyon güncellemesi ile aktif edilecek:
# VAKIFBANK_VPP_MERCHANT_ID  = os.environ.get('VAKIFBANK_VPP_MERCHANT_ID', '')
# VAKIFBANK_VPP_TERMINAL_ID  = os.environ.get('VAKIFBANK_VPP_TERMINAL_ID', '')
# VAKIFBANK_VPP_PASSWORD      = os.environ.get('VAKIFBANK_VPP_PASSWORD', '')
# VAKIFBANK_VPP_BASE_URL      = os.environ.get('VAKIFBANK_VPP_BASE_URL', '')

# ── E-posta (SMTP) ─────────────────────────────────────────────────────────────
# Graceful degradation: if not configured, falls back to console email backend
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # Default: print to stdout
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@facesyma.com')

# ── Slack Webhook (Uyarılar için) ───────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

# ── Medya dosyaları ────────────────────────────────────────────────────────────
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL  = '/media/'
UPLOAD_TMP = MEDIA_ROOT / 'tmp'

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://facesyma.com,http://localhost:3000,http://localhost:8080'
).split(',')
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
    'x-app-source',  # Multi-app: web/mobile ayrımı
]

# ── Security Headers ──────────────────────────────────────────────────────────
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',   # Anonim kullanıcılar
        'user': '120/minute',  # Authenticated kullanıcılar
    },
}

# ── Templates ──────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'admin_api' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

# ── Cache (Redis öncelikli, fallback in-memory) ────────────────────────────────
_redis_host = os.environ.get('REDIS_HOST', 'redis')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f"redis://{_redis_host}:{os.environ.get('REDIS_PORT', '6379')}/4",
        'TIMEOUT': 300,
        'OPTIONS': {
            'socket_connect_timeout': 3,
            'socket_timeout': 3,
            'CONNECTION_POOL_KWARGS': {'max_connections': 20},
        },
        'KEY_PREFIX': 'facesyma',
    }
} if _redis_host else {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,
    }
}

# ── Static ─────────────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# ── Dil / Zaman dilimi ─────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-US'  # Default: English
TIME_ZONE     = 'Europe/Istanbul'
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True

# ── Desteklenen Diller (18 dil) ────────────────────────────────────────────────
LANGUAGES = [
    ('en', 'English'),
    ('tr', 'Türkçe'),
    ('de', 'Deutsch'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('pt', 'Português'),
    ('pl', 'Polski'),
    ('ru', 'Русский'),
    ('ja', '日本語'),
    ('zh-hans', '简体中文'),
    ('zh-hant', '繁體中文'),
    ('ko', '한국어'),
    ('ar', 'العربية'),
    ('he', 'עברית'),
    ('hi', 'हिन्दी'),
    ('vi', 'Tiếng Việt'),
    ('th', 'ไทย'),
]

# ── Locale Dosyaları Yolu ──────────────────────────────────────────────────────
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'gamification' / 'locale',
    BASE_DIR / 'admin_api' / 'locale',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Yüz analiz motoru yolu ────────────────────────────────────────────────────
# facesyma_revize klasörü sunucuda nerede?
FACESYMA_ENGINE_PATH = os.environ.get(
    'FACESYMA_ENGINE_PATH',
    str(BASE_DIR.parent / 'facesyma_revize')
)

# ── Sıfat Veritabanı JSON yolu ────────────────────────────────────────────────
SIFAT_DB_PATH = os.environ.get(
    'SIFAT_DB_PATH',
    str(BASE_DIR.parent / 'facesyma_migrate' / 'sifat_veritabani.json')
)

# ── Google Translate API (Opsiyonel) ──────────────────────────────────────────
GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY', None)

# ── Servis URL'leri ────────────────────────────────────────────────────────────
# Her mikro servisin URL'i — tüm view'lar bu değerleri kullanır
AI_SERVICE_URL     = os.environ.get('AI_SERVICE_URL',     'http://localhost:8002')
COACH_SERVICE_URL  = os.environ.get('COACH_SERVICE_URL',  'http://localhost:8003')
FINETUNE_SERVICE_URL = os.environ.get('FINETUNE_SERVICE_URL', 'http://localhost:8002')

# ── Loglama ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{levelname}] {asctime} {module}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django':       {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'analysis_api': {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
        'auth_api':     {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
        'admin_api':    {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
        'gamification': {'handlers': ['console'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
    },
}

# ── Django Channels ────────────────────────────────────────────────────────────
ASGI_APPLICATION = 'facesyma_project.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', 'redis'), int(os.environ.get('REDIS_PORT', '6379')))],
            'db': int(os.environ.get('REDIS_CHANNELS_DB', '3')),
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# ── Multi-App Support ─────────────────────────────────────────────────────────
SUPPORTED_APP_SOURCES = ['mobile', 'web']
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://facesyma.com')
