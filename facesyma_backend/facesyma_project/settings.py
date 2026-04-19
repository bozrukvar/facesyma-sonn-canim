"""
facesyma_project/settings.py
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Güvenlik ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-in-production-xxx')
DEBUG      = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

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
    'django.middleware.locale.LocaleMiddleware',  # Language detection
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
    'mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/'
    'facesyma-backend?serverSelectionTimeoutMS=30000&connectTimeoutMS=30000&retryWrites=true'
)

# ── JWT ────────────────────────────────────────────────────────────────────────
JWT_SECRET  = os.environ.get('JWT_SECRET', 'facesyma-jwt-secret-change-in-production')
JWT_ACCESS_EXP_HOURS   = int(os.environ.get('JWT_ACCESS_EXP_HOURS', '1'))
JWT_REFRESH_EXP_DAYS   = int(os.environ.get('JWT_REFRESH_EXP_DAYS', '30'))

# ── Admin JWT ──────────────────────────────────────────────────────────────────
ADMIN_JWT_SECRET = os.environ.get('ADMIN_JWT_SECRET', 'facesyma-admin-jwt-secret-change-in-production')
ADMIN_JWT_EXP_HOURS = int(os.environ.get('ADMIN_JWT_EXP_HOURS', '8'))

# ── Google OAuth ───────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

# ── Payment Processing (Stripe & iyzico) ────────────────────────────────────────
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', 'sk_test_xxxxx')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_xxxxx')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_xxxxx')
IYZICO_API_KEY = os.environ.get('IYZICO_API_KEY', 'sandbox-key-xxx')
IYZICO_SECRET_KEY = os.environ.get('IYZICO_SECRET_KEY', 'sandbox-secret-xxx')
IYZICO_BASE_URL = 'https://sandbox-api.iyzipay.com'

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
        'analysis_api': {'handlers': ['console'], 'level': 'DEBUG',   'propagate': False},
        'auth_api':     {'handlers': ['console'], 'level': 'DEBUG',   'propagate': False},
        'admin_api':    {'handlers': ['console'], 'level': 'DEBUG',   'propagate': False},
        'gamification': {'handlers': ['console'], 'level': 'DEBUG',   'propagate': False},
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
