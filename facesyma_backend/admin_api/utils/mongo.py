"""
admin_api/utils/mongo.py
========================
MongoDB collection'larına merkezi erişim.
Connection pooling ve atomic ID generation ile optimize.
"""

import logging
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from django.conf import settings

log = logging.getLogger(__name__)

# ── Module-level singletons ────────────────────────────────────────────────────

_main_client: MongoClient | None = None
_coach_client: MongoClient | None = None


def _ensure_indexes(db) -> None:
    """Create critical indexes on first startup. Safe to call multiple times (no-ops if exist)."""
    try:
        # Users — login/registration queries hit email on every request
        users = db['appfaceapi_myuser']
        _uidx = users.create_index
        _uidx([('email', ASCENDING)], unique=True, sparse=True, background=True)
        _uidx([('id', ASCENDING)], unique=True, background=True)
        _uidx([('google_id', ASCENDING)], sparse=True, background=True)
        _uidx([('date_joined', DESCENDING)], background=True)
        _uidx([('app_source', ASCENDING), ('date_joined', DESCENDING)], background=True)

        # Analysis history — fetched per user, sorted by time
        history = db['analysis_history']
        _hci = history.create_index
        _hci([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        _hci([('app_source', ASCENDING), ('created_at', DESCENDING)], background=True)

        # Admin users
        admins = db['admin_users']
        _aci = admins.create_index
        _aci([('email', ASCENDING)], unique=True, sparse=True, background=True)
        _aci([('id', ASCENDING)], unique=True, background=True)

        # Compatibility analytics queries
        compat = db['compatibility']
        _cidx = compat.create_index
        _cidx([('category', ASCENDING)], background=True)
        _cidx([('score', ASCENDING)], background=True)
        _cidx([('user_id', ASCENDING)], background=True)

        log.info("✓ MongoDB indexes ensured")
    except Exception as e:
        log.warning(f"Index creation warning: {e}")


def _get_main_client() -> MongoClient:
    """Get shared MongoDB client with connection pooling for facesyma-backend"""
    global _main_client
    if _main_client is None:
        _main_client = MongoClient(
            settings.MONGO_URI,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            retryWrites=True,
        )
        _ensure_indexes(_main_client['facesyma-backend'])
        log.info("✓ MongoDB main client initialized (pool: 5-50 connections)")
    return _main_client


def _get_coach_client() -> MongoClient:
    """Get shared MongoDB client with connection pooling for facesyma-coach-backup"""
    global _coach_client
    if _coach_client is None:
        _coach_client = MongoClient(
            settings.MONGO_URI,
            maxPoolSize=30,
            minPoolSize=2,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
        )
        log.info("✓ MongoDB coach client initialized (pool: 2-30 connections)")
    return _coach_client


def _get_db():
    """Get facesyma-backend database with pooled connection"""
    return _get_main_client()['facesyma-backend']


def _get_backup_db():
    """Get facesyma-backups database with pooled connection"""
    return _get_main_client()['facesyma-backups']


def get_users_col():
    """appfaceapi_myuser collection"""
    return _get_db()['appfaceapi_myuser']


def get_history_col():
    """analysis_history collection"""
    return _get_db()['analysis_history']


def get_admin_col():
    """admin_users collection"""
    return _get_db()['admin_users']


def get_reviews_col():
    """reviews collection"""
    return _get_db()['reviews']


def get_plan_log_col():
    """plan_change_log collection"""
    return _get_db()['plan_change_log']


def get_app_registry_col():
    """app_registry collection — per-app status ve feature konfigürasyonu"""
    return _get_db()['app_registry']


def get_peer_chat_requests_col():
    """peer_chat_requests collection — sohbet onay istekleri"""
    return _get_db()['peer_chat_requests']


def get_peer_chat_rooms_col():
    """peer_chat_rooms collection — aktif sohbet odaları"""
    return _get_db()['peer_chat_rooms']


def get_peer_messages_col():
    """peer_messages collection — sohbet mesajları"""
    return _get_db()['peer_messages']


def _next_id(col) -> int:
    """
    Generate atomic auto-increment ID using counters collection.
    Replaces the old find_one(sort=[('id', -1)]) pattern which had race conditions.

    Uses MongoDB's atomic find_one_and_update to ensure no duplicate IDs
    under concurrent requests.
    """
    counters = _get_db()['_id_counters']
    result = counters.find_one_and_update(
        {'_id': col.name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result['seq']


# ── Coach DB (facesyma-coach-backup) ───────────────────────────────────────────

def _get_coach_db():
    """Get facesyma-coach-backup database with pooled connection"""
    return _get_coach_client()['facesyma-coach-backup']


def get_coach_users_col():
    """coach_users collection"""
    return _get_coach_db()['coach_users']


def get_coach_birth_col():
    """coach_birth_data collection"""
    return _get_coach_db()['coach_birth_data']


def get_coach_goals_col():
    """coach_goals collection"""
    return _get_coach_db()['coach_goals']


def get_coach_sessions_col():
    """coach_sessions collection"""
    return _get_coach_db()['coach_sessions']


def get_coach_attributes_col(lang: str):
    """
    coach_attributes_{lang} collection.
    lang must be one of the 18 supported languages.
    """
    return _get_coach_db()[f'coach_attributes_{lang}']


ALL_COACH_LANGS = [
    "tr", "en", "de", "ru", "ar", "es", "ko", "ja",
    "zh", "hi", "fr", "pt", "bn", "id", "ur", "it", "vi", "pl"
]

ALL_COACH_MODULES = [
    "kariyer", "giyim", "liderlik", "duygusal", "uyum", "beceri",
    "ik", "tavsiye", "motivasyon", "astroloji", "etkinlik", "muzik",
    "film_dizi", "saglik_esenwlik", "dogruluk_sadakat", "guvenlik",
    "suc_egilim", "iliski_yonetimi", "iletisim_becerileri",
    "stres_yonetimi", "ozguven", "zaman_yonetimi", "kisisel_hedefler",
    "astroloji_harita", "dogum_analizi", "yas_koc_ozet", "vucut_dil"
]


# ── Compatibility & Communities (Phase 1) ──────────────────────────────────────

def get_compatibility_col():
    """compatibility collection — uyum skorları ve kategorileri"""
    return _get_db()['compatibility']


def get_communities_col():
    """communities collection — sıfat/modül/kategori toplulukları"""
    return _get_db()['communities']


def get_community_members_col():
    """community_members collection — topluluk üyelikleri ve uyum seviyeleri"""
    return _get_db()['community_members']


def get_community_messages_col():
    """community_messages collection — topluluklardaki mesajlar"""
    return _get_db()['community_messages']


def get_community_files_col():
    """community_files collection — dosya depolaması ve meta verisi"""
    return _get_db()['community_files']


def get_moderation_logs_col():
    """moderation_logs collection — topluluklardaki moderasyon eylemleri"""
    return _get_db()['moderation_logs']


# ── Assessment Results (Phase 5) ──────────────────────────────────────────────

def get_assessment_results_col():
    """assessment_results collection — kişilik testleri sonuçları"""
    return _get_db()['assessment_results']
