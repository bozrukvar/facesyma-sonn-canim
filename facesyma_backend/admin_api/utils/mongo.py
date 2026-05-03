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
_test_client: MongoClient | None = None


def _ensure_indexes(db) -> None:
    """Create all indexes on first startup. Safe to call multiple times (no-ops if exist)."""
    try:
        # ── Users ──────────────────────────────────────────────────────────────
        users = db['appfaceapi_myuser']
        _uidx = users.create_index
        _uidx([('email', ASCENDING)], unique=True, sparse=True, background=True)
        _uidx([('id', ASCENDING)], unique=True, background=True)
        _uidx([('google_id', ASCENDING)], sparse=True, background=True)
        _uidx([('date_joined', DESCENDING)], background=True)
        _uidx([('app_source', ASCENDING), ('date_joined', DESCENDING)], background=True)
        # Gamification / leaderboard alanları
        _uidx([('coins', DESCENDING)], sparse=True, background=True)
        _uidx([('total_earned', DESCENDING)], sparse=True, background=True)
        _uidx([('streak_count', DESCENDING)], sparse=True, background=True)
        _uidx([('last_daily_quest', ASCENDING)], sparse=True, background=True)

        # ── Analysis history ───────────────────────────────────────────────────
        history = db['analysis_history']
        history.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        history.create_index([('app_source', ASCENDING), ('created_at', DESCENDING)], background=True)

        # ── Admin users ────────────────────────────────────────────────────────
        admins = db['admin_users']
        admins.create_index([('email', ASCENDING)], unique=True, sparse=True, background=True)
        admins.create_index([('id', ASCENDING)], unique=True, background=True)

        # ── Compatibility ──────────────────────────────────────────────────────
        compat = db['compatibility']
        compat.create_index([('category', ASCENDING)], background=True)
        compat.create_index([('score', ASCENDING)], background=True)
        compat.create_index([('user_id', ASCENDING)], background=True)

        # ── Communities ────────────────────────────────────────────────────────
        communities = db['communities']
        communities.create_index([('type', ASCENDING)], background=True)
        communities.create_index([('type', ASCENDING), ('trait_name', ASCENDING)], background=True)
        communities.create_index([('is_active', ASCENDING)], background=True)

        # ── Community members — WS auth hot path ───────────────────────────────
        comm_members = db['community_members']
        comm_members.create_index(
            [('community_id', ASCENDING), ('user_id', ASCENDING)],
            unique=True, background=True,
        )
        comm_members.create_index([('user_id', ASCENDING), ('status', ASCENDING)], background=True)

        # ── Community messages ─────────────────────────────────────────────────
        comm_msgs = db['community_messages']
        comm_msgs.create_index([('community_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        comm_msgs.create_index([('community_id', ASCENDING), ('read_by', ASCENDING)], background=True)
        comm_msgs.create_index([('sender_id', ASCENDING)], background=True)

        # ── Community missions ─────────────────────────────────────────────────
        missions = db['community_missions']
        missions.create_index([('mission_id', ASCENDING)], unique=True, background=True)
        missions.create_index([('status', ASCENDING), ('end_time', ASCENDING)], background=True)
        missions.create_index([('community_id', ASCENDING), ('status', ASCENDING)], sparse=True, background=True)
        missions.create_index([('participants.user_id', ASCENDING)], sparse=True, background=True)

        # ── Peer chat ──────────────────────────────────────────────────────────
        peer_requests = db['peer_chat_requests']
        peer_requests.create_index([('to_user_id', ASCENDING), ('status', ASCENDING)], background=True)
        peer_requests.create_index([('from_user_id', ASCENDING)], background=True)
        peer_rooms = db['peer_chat_rooms']
        peer_rooms.create_index([('participants', ASCENDING)], background=True)
        peer_msgs = db['peer_messages']
        peer_msgs.create_index([('room_id', ASCENDING), ('created_at', DESCENDING)], background=True)

        # ── Gamification ───────────────────────────────────────────────────────
        snap = db['leaderboard_snapshots']
        snap.create_index([('snapshot_id', ASCENDING)], unique=True, background=True)
        snap.create_index([('leaderboard_type', ASCENDING), ('taken_at', DESCENDING)], background=True)
        snap.create_index([('trait_id', ASCENDING), ('taken_at', DESCENDING)], sparse=True, background=True)
        snap.create_index([('community_id', ASCENDING), ('taken_at', DESCENDING)], sparse=True, background=True)

        badges = db['user_badges']
        badges.create_index([('user_id', ASCENDING), ('badge_id', ASCENDING)], unique=True, background=True)
        badges.create_index([('badge_id', ASCENDING), ('awarded_at', DESCENDING)], background=True)
        badges.create_index([('user_id', ASCENDING), ('awarded_at', DESCENDING)], background=True)

        game_sessions = db['discovery_game_sessions']
        game_sessions.create_index([('session_id', ASCENDING)], unique=True, background=True)
        game_sessions.create_index([('user_id', ASCENDING), ('started_at', DESCENDING)], background=True)
        game_sessions.create_index([('state', ASCENDING), ('updated_at', DESCENDING)], background=True)

        social_ch = db['social_challenges']
        social_ch.create_index([('status', ASCENDING), ('end_time', ASCENDING)], background=True)
        social_ch.create_index([('community_id', ASCENDING), ('status', ASCENDING)], sparse=True, background=True)
        social_ch.create_index([('participants.user_id', ASCENDING)], sparse=True, background=True)
        social_ch.create_index([('created_at', DESCENDING)], background=True)

        # ── Coins & ödemeler ───────────────────────────────────────────────────
        coin_tx = db['coin_transactions']
        coin_tx.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        coin_tx.create_index([('user_id', ASCENDING), ('type', ASCENDING)], background=True)
        coin_tx.create_index([('created_at', DESCENDING)], background=True)

        pay_tx = db['payment_transactions']
        pay_tx.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        pay_tx.create_index([('status', ASCENDING), ('created_at', DESCENDING)], background=True)

        pay_ref = db['payment_refunds']
        pay_ref.create_index([('transaction_id', ASCENDING)], background=True)
        pay_ref.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)

        # ── Abonelikler ────────────────────────────────────────────────────────
        subs = db['user_subscriptions']
        subs.create_index([('user_id', ASCENDING)], unique=True, background=True)
        subs.create_index([('status', ASCENDING)], background=True)
        subs.create_index([('expiry_date', ASCENDING)], background=True)

        sub_events = db['subscription_events']
        sub_events.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        sub_events.create_index([('event_type', ASCENDING), ('created_at', DESCENDING)], background=True)

        sub_notif = db['subscription_notifications']
        sub_notif.create_index([('user_id', ASCENDING), ('status', ASCENDING)], background=True)
        sub_notif.create_index([('scheduled_at', ASCENDING), ('status', ASCENDING)], background=True)

        # ── Kişilik testleri ───────────────────────────────────────────────────
        assessment = db['assessment_results']
        assessment.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        assessment.create_index([('user_id', ASCENDING), ('test_type', ASCENDING)], background=True)

        # ── Benzerlik koleksiyonları (art match) ───────────────────────────────
        for _sim in ('similarities_celebrities', 'similarities_historical',
                     'similarities_objects', 'similarities_plants', 'similarities_animals'):
            _sc = db[_sim]
            _sc.create_index([('user_id', ASCENDING)], background=True)
            _sc.create_index([('score', DESCENDING)], background=True)

        # ── Chat context cache ──────────────────────────────────────────────────
        for _cache in ('analysis_cache', 'compatibility_cache', 'user_profiles', 'chat_context_stats'):
            db[_cache].create_index([('user_id', ASCENDING)], unique=True, background=True)

        # ── Admin monitoring ───────────────────────────────────────────────────
        act_log = db['admin_activity_log']
        act_log.create_index([('created_at', DESCENDING)], background=True)
        act_log.create_index([('admin_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        act_log.create_index([('action_type', ASCENDING), ('created_at', DESCENDING)], background=True)

        alert_rules = db['alert_rules']
        alert_rules.create_index([('is_active', ASCENDING)], background=True)
        alert_rules.create_index([('metric_name', ASCENDING)], background=True)

        alert_hist = db['alert_history']
        alert_hist.create_index([('rule_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        alert_hist.create_index([('status', ASCENDING), ('created_at', DESCENDING)], background=True)

        svc_health = db['service_health']
        svc_health.create_index([('service_name', ASCENDING), ('checked_at', DESCENDING)], background=True)

        svc_metrics = db['service_metrics']
        svc_metrics.create_index([('service_name', ASCENDING), ('timestamp', DESCENDING)], background=True)

        uptime = db['uptime_logs']
        uptime.create_index([('service_name', ASCENDING), ('checked_at', DESCENDING)], background=True)

        err_logs = db['error_logs']
        err_logs.create_index([('created_at', DESCENDING)], background=True)
        err_logs.create_index([('service_name', ASCENDING), ('error_type', ASCENDING)], background=True)

        api_logs = db['api_logs']
        api_logs.create_index([('created_at', DESCENDING)], background=True)
        api_logs.create_index([('endpoint', ASCENDING), ('created_at', DESCENDING)], background=True)
        api_logs.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], sparse=True, background=True)

        alerts = db['alerts']
        alerts.create_index([('status', ASCENDING), ('severity', ASCENDING)], background=True)
        alerts.create_index([('created_at', DESCENDING)], background=True)

        sys_logs = db['system_logs']
        sys_logs.create_index([('created_at', DESCENDING)], background=True)
        sys_logs.create_index([('log_level', ASCENDING), ('service', ASCENDING)], background=True)

        # ── Moderasyon ─────────────────────────────────────────────────────────
        reports = db['user_reports']
        reports.create_index([('status', ASCENDING), ('created_at', DESCENDING)], background=True)
        reports.create_index([('reported_user_id', ASCENDING), ('status', ASCENDING)], background=True)

        mod_actions = db['moderation_actions']
        mod_actions.create_index([('target_user_id', ASCENDING), ('created_at', DESCENDING)], background=True)
        mod_actions.create_index([('moderator_id', ASCENDING), ('created_at', DESCENDING)], background=True)

        bans = db['ban_records']
        bans.create_index([('user_id', ASCENDING), ('is_active', ASCENDING)], background=True)
        bans.create_index([('expires_at', ASCENDING)], sparse=True, background=True)

        # ── Engagement / kampanyalar ───────────────────────────────────────────
        push = db['push_campaigns']
        push.create_index([('status', ASCENDING), ('scheduled_at', ASCENDING)], background=True)
        push.create_index([('created_at', DESCENDING)], background=True)

        notif_tmpl = db['notification_templates']
        notif_tmpl.create_index([('template_id', ASCENDING)], unique=True, background=True)
        notif_tmpl.create_index([('type', ASCENDING)], background=True)

        email_camp = db['email_campaigns']
        email_camp.create_index([('status', ASCENDING), ('scheduled_at', ASCENDING)], background=True)
        email_camp.create_index([('created_at', DESCENDING)], background=True)

        # ── İçerik ────────────────────────────────────────────────────────────
        coach_content = db['coaching_content']
        coach_content.create_index([('module', ASCENDING), ('lang', ASCENDING)], background=True)
        coach_content.create_index([('user_id', ASCENDING)], sparse=True, background=True)
        coach_content.create_index([('created_at', DESCENDING)], background=True)

        ab_tests = db['ab_tests']
        ab_tests.create_index([('name', ASCENDING)], unique=True, background=True)
        ab_tests.create_index([('status', ASCENDING)], background=True)

        templates = db['content_templates']
        templates.create_index([('type', ASCENDING), ('created_at', DESCENDING)], background=True)

        # ── Yedekleme ──────────────────────────────────────────────────────────
        backups = db['backup_records']
        backups.create_index([('backup_id', ASCENDING)], unique=True, background=True)
        backups.create_index([('status', ASCENDING), ('created_at', DESCENDING)], background=True)

        backup_sched = db['backup_schedules']
        backup_sched.create_index([('schedule_id', ASCENDING)], unique=True, background=True)
        backup_sched.create_index([('is_active', ASCENDING), ('next_run', ASCENDING)], background=True)

        restore = db['restore_logs']
        restore.create_index([('backup_id', ASCENDING)], background=True)
        restore.create_index([('created_at', DESCENDING)], background=True)

        # ── Uygulama kaydı / raporlama / diğer ────────────────────────────────
        app_reg = db['app_registry']
        app_reg.create_index([('app_id', ASCENDING)], unique=True, background=True)
        app_reg.create_index([('platform', ASCENDING)], background=True)

        plan_log = db['plan_change_log']
        plan_log.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)

        gen_reports = db['generated_reports']
        gen_reports.create_index([('report_type', ASCENDING), ('created_at', DESCENDING)], background=True)

        sched_reports = db['scheduled_reports']
        sched_reports.create_index([('is_active', ASCENDING), ('next_run', ASCENDING)], background=True)

        reviews = db['reviews']
        reviews.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)], background=True)

        # ── FCM device tokens — sparse so users without tokens are excluded ──
        users_col = db['appfaceapi_myuser']
        users_col.create_index(
            [('device_token', ASCENDING)],
            sparse=True, background=True
        )

        # ── Archetype pool + rotation history ─────────────────────────────
        archetype_pool = db['archetype_pool']
        archetype_pool.create_index([('type', ASCENDING)], background=True)
        archetype_pool.create_index([('id', ASCENDING)], unique=True, background=True)

        archetype_history = db['user_archetype_history']
        archetype_history.create_index([('user_id', ASCENDING)], unique=True, background=True)

        # ── Art pool + rotation history ────────────────────────────────────
        art_pool = db['art_pool']
        art_pool.create_index([('id', ASCENDING)], unique=True, background=True)
        art_pool.create_index([('has_portrait', ASCENDING)], background=True)

        art_history = db['user_art_history']
        art_history.create_index([('user_id', ASCENDING)], unique=True, background=True)

        # ── AI long-term memory ────────────────────────────────────────────
        ai_mem = db['ai_user_memory']
        ai_mem.create_index([('user_id', ASCENDING)], unique=True, background=True)

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


def _get_test_client() -> MongoClient:
    """Test servisinin MongoDB cluster'ına bağlanır (TEST_MONGO_URI ayrı olabilir)."""
    global _test_client
    if _test_client is None:
        from django.conf import settings
        uri = getattr(settings, 'TEST_MONGO_URI', settings.MONGO_URI)
        _test_client = MongoClient(
            uri,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        log.info("✓ MongoDB test client initialized")
    return _test_client


def get_test_results_col():
    """facesyma-test-backup.test_results — psikolojik test sonuçları"""
    return _get_test_client()['facesyma-test-backup']['test_results']


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
    "astroloji_harita", "dogum_analizi", "yas_koc_ozet", "vucut_dil",
    # Tip A — yeni text modüller
    "etkinlik_tavsiye", "spor_aktivite", "kariyer_yolu",
    "insan_kaynaklari", "duygusal_ruhsal", "meditasyon_egzersiz",
    # Tip B — yeni dict/JSON modüller
    "kitap_tavsiye", "film_tavsiye", "muzik_tavsiye",
    "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon", "saglik_tavsiye",
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


# ── Subscriptions & Payments ──────────────────────────────────────────────────

def get_user_subscriptions_col():
    """user_subscriptions collection — aktif abonelik kayıtları"""
    return _get_db()['user_subscriptions']


def get_subscription_events_col():
    """subscription_events collection — yenileme/iptal olayları"""
    return _get_db()['subscription_events']


def get_subscription_notifications_col():
    """subscription_notifications collection — abonelik bildirimleri"""
    return _get_db()['subscription_notifications']


# ── Reporting ─────────────────────────────────────────────────────────────────

def get_generated_reports_col():
    """generated_reports collection — oluşturulan raporlar"""
    return _get_db()['generated_reports']


def get_scheduled_reports_col():
    """scheduled_reports collection — zamanlanmış rapor tanımları"""
    return _get_db()['scheduled_reports']


# ── Campaigns & Engagement ────────────────────────────────────────────────────

def get_push_campaigns_col():
    """push_campaigns collection — push bildirim kampanyaları"""
    return _get_db()['push_campaigns']


def get_notification_templates_col():
    """notification_templates collection — bildirim şablonları"""
    return _get_db()['notification_templates']


def get_email_campaigns_col():
    """email_campaigns collection — e-posta kampanyaları"""
    return _get_db()['email_campaigns']
