"""
mongo_store.py
==============
Diyet koçluğu için MongoDB kalıcılık katmanı.

Koleksiyonlar:
  diet_recommendations — günlük tavsiyeler (geçmiş + tekrar önleme)
  diet_feedback        — kullanıcı geri bildirimleri

MongoDB bağlanamadığında sessizce devre dışı kalır (graceful degrade).
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

log = logging.getLogger(__name__)

_client = None
_db     = None
_UNAVAILABLE = False   # True olursa bağlantı denemesinden vazgeçilir


def _get_db():
    global _client, _db, _UNAVAILABLE
    if _UNAVAILABLE:
        return None
    if _db is not None:
        return _db
    try:
        import pymongo
        uri = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/facesyma")
        _client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
        _client.admin.command("ping")           # bağlantıyı doğrula
        _db = _client.get_default_database()
        log.info("✓ Diet MongoDB bağlantısı kuruldu")
        return _db
    except Exception as exc:
        _UNAVAILABLE = True
        log.warning(f"Diet MongoDB bağlanamadı — belleksiz modda çalışılacak: {exc}")
        return None


# ── Tavsiye Kaydet ─────────────────────────────────────────────────────────────

def save_recommendation(
    user_id: int,
    country_code: str,
    language_code: str,
    recommendation: Dict[str, Any],
) -> bool:
    """
    Günlük tavsiyeyi kaydet. Aynı gün için varsa güncelle (upsert).
    recommendation: DailyRecommendation.dict() çıktısı
    """
    db = _get_db()
    if db is None:
        return False
    try:
        date = recommendation.get("date") or datetime.utcnow().strftime("%Y-%m-%d")

        def _first_id(key: str) -> Optional[str]:
            items = recommendation.get(key, [])
            return items[0].get("meal_id") if items else None

        doc = {
            "user_id":       user_id,
            "date":          date,
            "country_code":  country_code,
            "language_code": language_code,
            "breakfast_id":  _first_id("breakfast"),
            "lunch_id":      _first_id("lunch"),
            "dinner_id":     _first_id("dinner"),
            "breakfast_name": (recommendation.get("breakfast") or [{}])[0].get("name"),
            "lunch_name":     (recommendation.get("lunch")     or [{}])[0].get("name"),
            "dinner_name":    (recommendation.get("dinner")    or [{}])[0].get("name"),
            "user_sifats":   recommendation.get("user_sifats", []),
            "updated_at":    datetime.utcnow(),
        }
        db.diet_recommendations.update_one(
            {"user_id": user_id, "date": date},
            {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )
        return True
    except Exception as exc:
        log.warning(f"save_recommendation hatası: {exc}")
        return False


# ── Öğün Geçmişi ──────────────────────────────────────────────────────────────

def get_recent_meal_ids(user_id: int, days: int = 7) -> List[str]:
    """
    Son N gündeki önerilen yemeklerin ID listesini döndür.
    Tekrar önleme için UserProfile.last_7_meals yerine kullanılır.
    """
    db = _get_db()
    if db is None:
        return []
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        docs = list(db.diet_recommendations.find(
            {"user_id": user_id, "date": {"$gte": cutoff}},
            {"breakfast_id": 1, "lunch_id": 1, "dinner_id": 1},
        ))
        ids = []
        for d in docs:
            for key in ("breakfast_id", "lunch_id", "dinner_id"):
                v = d.get(key)
                if v:
                    ids.append(v)
        return ids
    except Exception as exc:
        log.warning(f"get_recent_meal_ids hatası: {exc}")
        return []


def get_recommendation_history(user_id: int, limit: int = 7) -> List[Dict[str, Any]]:
    """Son N günlük tavsiye özetlerini döndür (tarih + ana yemek adları)."""
    db = _get_db()
    if db is None:
        return []
    try:
        docs = list(
            db.diet_recommendations.find(
                {"user_id": user_id},
                {"_id": 0, "user_id": 0, "updated_at": 0},
            ).sort("date", -1).limit(limit)
        )
        return docs
    except Exception as exc:
        log.warning(f"get_recommendation_history hatası: {exc}")
        return []


# ── Geri Bildirim ─────────────────────────────────────────────────────────────

def save_feedback(
    user_id: int,
    meal_id: str,
    meal_type: str,
    date: str,
    feedback: str,
) -> bool:
    """Kullanıcının yemek geri bildirimini kaydet (upsert)."""
    db = _get_db()
    if db is None:
        return False
    try:
        db.diet_feedback.update_one(
            {"user_id": user_id, "meal_id": meal_id, "date": date},
            {
                "$set": {
                    "meal_type":  meal_type,
                    "feedback":   feedback,
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.utcnow()},
            },
            upsert=True,
        )
        return True
    except Exception as exc:
        log.warning(f"save_feedback hatası: {exc}")
        return False


def get_user_feedback(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Kullanıcının son geri bildirimlerini döndür."""
    db = _get_db()
    if db is None:
        return []
    try:
        docs = list(
            db.diet_feedback.find(
                {"user_id": user_id},
                {"_id": 0},
            ).sort("created_at", -1).limit(limit)
        )
        return docs
    except Exception as exc:
        log.warning(f"get_user_feedback hatası: {exc}")
        return []
