"""
chat_context_builder.py
=======================
Ollama LLM için context oluşturur.
- analysisResult cache'ten alır (30-day TTL)
- Compatibility data'sını ekler (eğer var)
- Image quality metrics'ini ekler
- Formatted JSON → Chat API'ye gönderir

Veritabanı:
  - analysis_cache (TTL: 30 days)
  - compatibility_cache (TTL: 30 days)
  - user_profiles (user_id → partner_id mapping)
"""

import json
import logging
import time
from pymongo import MongoClient
from django.conf import settings

log = logging.getLogger(__name__)


# ── MongoDB Bağlantı ──────────────────────────────────────────────────────────
def _get_db():
    """Get facesyma-backend database with pooled connection"""
    from admin_api.utils.mongo import _get_main_client
    return _get_main_client()['facesyma-backend']


def _get_analysis_cache_col():
    """analysis_cache koleksiyonunu al ve TTL index oluştur"""
    db = _get_db()
    col = db['analysis_cache']

    # TTL index: 30 gün = 2592000 saniye
    try:
        col.create_index('created_at', expireAfterSeconds=2592000)
    except Exception as e:
        log.warning(f'TTL index oluşturma başarısız: {e}')

    return col


def _get_compatibility_cache_col():
    """compatibility_cache koleksiyonunu al ve TTL index oluştur"""
    db = _get_db()
    col = db['compatibility_cache']

    try:
        col.create_index('created_at', expireAfterSeconds=2592000)
    except Exception as e:
        log.warning(f'TTL index oluşturma başarısız: {e}')

    return col


def _get_user_profiles_col():
    """user_profiles koleksiyonunu al (partner_id mapping)"""
    return _get_db()['user_profiles']


# ── Context Builder Functions ──────────────────────────────────────────────────

def cache_analysis_result(user_id: int, lang: str, analysis_result: dict, photo_hash: str = None):
    """
    analysisResult'ı MongoDB'de cache'le.

    Args:
        user_id: Kullanıcı ID
        lang: Dil (tr, en, de, etc.)
        analysis_result: Analysis'ten dönen result
        photo_hash: Content-based hash (optional, deduplication için)
    """
    try:
        col = _get_analysis_cache_col()

        # Unique key: user_id + lang + photo_hash
        filter_doc = {
            'user_id': user_id,
            'lang': lang,
            'photo_hash': photo_hash or 'latest'
        }

        update_doc = {
            'user_id': user_id,
            'lang': lang,
            'photo_hash': photo_hash or 'latest',
            'result': analysis_result,
            'created_at': time.time(),
            'accessed_at': time.time()
        }

        col.update_one(filter_doc, {'$set': update_doc}, upsert=True)
        log.info(f'Analysis cache saved: user_id={user_id}, lang={lang}')

    except Exception as e:
        log.error(f'Analysis cache kaydedilemedi: {e}')


def get_analysis_result(user_id: int, lang: str, use_latest: bool = True) -> dict | None:
    """
    Cache'ten analysisResult'ı al.

    Args:
        user_id: Kullanıcı ID
        lang: Dil
        use_latest: En yeni result'ı al (photo_hash yoksay)

    Returns:
        {'user_id', 'lang', 'result': {...}, 'accessed_at'}
        veya None (cache miss)
    """
    try:
        col = _get_analysis_cache_col()

        if use_latest:
            # En yeni result'ı al (created_at'a göre)
            doc = col.find_one(
                {'user_id': user_id, 'lang': lang},
                sort=[('created_at', -1)]
            )
        else:
            # En son kullanılan
            doc = col.find_one(
                {'user_id': user_id, 'lang': lang},
                sort=[('accessed_at', -1)]
            )

        if doc:
            # accessed_at'i güncelle
            col.update_one(
                {'_id': doc['_id']},
                {'$set': {'accessed_at': time.time()}}
            )
            log.info(f'Analysis cache hit: user_id={user_id}, lang={lang}')
            return doc

        log.warning(f'Analysis cache miss: user_id={user_id}, lang={lang}')
        return None

    except Exception as e:
        log.error(f'Analysis cache okunamadı: {e}')
        return None


def get_user_partner_id(user_id: int) -> int | None:
    """
    Kullanıcının partner_id'sini al.

    Returns:
        partner_id veya None
    """
    try:
        col = _get_user_profiles_col()
        profile = col.find_one({'user_id': user_id}, {'partner_id': 1})
        return profile.get('partner_id') if profile else None
    except Exception as e:
        log.warning(f'Partner ID alınamadı: {e}')
        return None


def cache_compatibility(user1_id: int, user2_id: int, compatibility_result: dict):
    """
    Compatibility result'ını cache'le.

    Args:
        user1_id, user2_id: Kullanıcı IDs
        compatibility_result: /compatibility/check/ endpoint'inden dönen result
    """
    try:
        col = _get_compatibility_cache_col()

        # Düşük ID'yi başa koy (symmetry)
        uid1, uid2 = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)

        doc = {
            'user1_id': uid1,
            'user2_id': uid2,
            'score': compatibility_result.get('score', 0),
            'category': compatibility_result.get('category', 'UNKNOWN'),
            'can_message': compatibility_result.get('can_message', False),
            'golden_ratio_diff': compatibility_result.get('golden_ratio_diff', 0),
            'sifat_overlap': compatibility_result.get('sifat_overlap', 0),
            'module_overlap': compatibility_result.get('module_overlap', 0),
            'conflict_count': compatibility_result.get('conflict_count', 0),
            'result': compatibility_result,
            'created_at': time.time()
        }

        col.update_one(
            {'user1_id': uid1, 'user2_id': uid2},
            {'$set': doc},
            upsert=True
        )
        log.info(f'Compatibility cache saved: {uid1} ↔ {uid2}')

    except Exception as e:
        log.error(f'Compatibility cache kaydedilemedi: {e}')


def get_compatibility(user1_id: int, user2_id: int) -> dict | None:
    """
    Cache'ten compatibility'yi al.

    Returns:
        {'user1_id', 'user2_id', 'score', 'category', ...}
        veya None (cache miss)
    """
    try:
        col = _get_compatibility_cache_col()

        # Düşük ID'yi başa koy
        uid1, uid2 = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)

        doc = col.find_one({'user1_id': uid1, 'user2_id': uid2})

        if doc:
            log.info(f'Compatibility cache hit: {uid1} ↔ {uid2}')
            return doc

        log.warning(f'Compatibility cache miss: {uid1} ↔ {uid2}')
        return None

    except Exception as e:
        log.error(f'Compatibility cache okunamadı: {e}')
        return None


# ── Main Context Builder ───────────────────────────────────────────────────────

def build_ollama_context(user_id: int, lang: str = 'tr', partner_id: int | None = None) -> dict:
    """
    Ollama LLM için context oluştur.

    Yapı:
    {
        'user': {...analysis_result...},
        'partner': {...analysis_result...} (eğer var),
        'compatibility': {...uyum...} (eğer var),
        'context_built_at': timestamp
    }

    Args:
        user_id: Ana kullanıcı ID
        lang: Dil
        partner_id: Partner ID (optional)

    Returns:
        Context dict (Ollama prompt'unda kullanılacak)
    """
    try:
        context = {
            'user_id': user_id,
            'lang': lang,
            'context_built_at': time.time(),
            'user': None,
            'partner': None,
            'compatibility': None
        }

        # 1. User'ın analysisResult'ını al
        user_analysis = get_analysis_result(user_id, lang)
        if user_analysis:
            context['user'] = user_analysis.get('result', {})
            log.info(f'User analysis loaded from cache: user_id={user_id}')
        else:
            log.warning(f'User analysis not found: user_id={user_id}')
            return context  # Boş context dön

        # 2. Partner ID'sini al (eğer sağlanmadıysa)
        if not partner_id:
            partner_id = get_user_partner_id(user_id)

        # 3. Partner analysisResult'ını al (eğer var)
        if partner_id:
            partner_analysis = get_analysis_result(partner_id, lang)
            if partner_analysis:
                context['partner'] = partner_analysis.get('result', {})
                log.info(f'Partner analysis loaded: partner_id={partner_id}')

                # 4. Compatibility'yi al
                compat = get_compatibility(user_id, partner_id)
                if compat:
                    context['compatibility'] = {
                        'score': compat.get('score'),
                        'category': compat.get('category'),
                        'can_message': compat.get('can_message'),
                        'golden_ratio_diff': compat.get('golden_ratio_diff'),
                        'sifat_overlap': compat.get('sifat_overlap'),
                        'module_overlap': compat.get('module_overlap'),
                        'conflict_count': compat.get('conflict_count')
                    }
                    log.info(f'Compatibility loaded: {user_id} ↔ {partner_id}')

        return context

    except Exception as e:
        log.exception(f'Context building hatası: {e}')
        return {
            'user_id': user_id,
            'lang': lang,
            'context_built_at': time.time(),
            'user': None,
            'partner': None,
            'compatibility': None,
            'error': str(e)
        }


def format_context_for_prompt(context: dict) -> str:
    """
    Context'i Ollama system prompt'unda kullanılabilir formata çevir.

    Returns:
        Formatted string (JSON)
    """
    try:
        return json.dumps(context, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f'Context formatting hatası: {e}')
        return '{}'
