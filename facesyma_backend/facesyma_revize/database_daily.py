import os
import numpy as np
from calculator import *
from pymongo import MongoClient
import random

# ── Module-level cache ────────────────────────────────────────────────────────
_mongo_client = None
_daily_words_cache = {}  # {db_name: {'positive': [...], 'negative': [...]}}

_LANG_DB_MAP = {
    "tr": "database_daily_tr", "tr-TR": "database_daily_tr",
    "de": "database_daily_de", "de-DE": "database_daily_de",
    "ru": "database_daily_ru", "ru-RU": "database_daily_ru",
    "ar": "database_daily_ar", "ar-AR": "database_daily_ar",
    "en": "database_daily_en", "en-US": "database_daily_en",
}


def _get_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(os.environ.get('MONGO_URI', ""))
    return _mongo_client


def _load_daily_words(db_name: str) -> dict:
    global _daily_words_cache
    if db_name in _daily_words_cache:
        return _daily_words_cache[db_name]
    dbref = _get_client()[db_name]
    pos_doc = dbref["positive"].find_one({}, {"_id": 0, "positive_daily": 1})
    neg_doc = dbref["negative"].find_one({}, {"_id": 0, "negative_daily": 1})
    words = {
        'positive': (pos_doc or {}).get('positive_daily', []),
        'negative': (neg_doc or {}).get('negative_daily', []),
    }
    _daily_words_cache[db_name] = words
    return words


def daily(img, user_id, lang):
    result = Cal(img)
    _r0 = _r0; _r1 = _r1; _r2 = _r2; _r3 = _r3; _r4 = _r4

    _lmget = _LANG_DB_MAP.get
    db_name = _lmget(lang, _lmget(lang.split('-')[0] if lang else '', "database_daily_en"))
    words = _load_daily_words(db_name)

    client = _get_client()
    golden_rate = client['facesyma-backend']["appfaceapi_myuser"]
    user = golden_rate.find_one({"id": int(user_id)}, {"_id": 0, "golden_mean": 1})

    array_mean = [
        _r0['eyes_size_l_rate'], _r0['eyes_size_r_rate'], _r0['eyes_distance_rate'],
        _r1['eyebrows_eyes_distance_l_rate'], _r1['eyebrows_eyes_distance_r_rate'],
        _r2['lips_width_rate'], _r2['lips_height_compare_rate'], _r2['lips_thickness_rate'],
        _r3['nose_length_rate'], _r3['nose_width_rate'],
        _r4['forehead_distance_rate'],
    ]

    final_mean = round(float(np.mean(array_mean)), 4)
    old_value = user['golden_mean']

    golden_rate.update_one({'golden_mean': old_value}, {"$set": {'golden_mean': final_mean}})

    if old_value <= final_mean:
        user_text = words['positive']
    else:
        user_text = words['negative']

    return random.choice(user_text) if user_text else ''
