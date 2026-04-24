import os
import random
from calculator import *
from pymongo import MongoClient

# ── Module-level cache ────────────────────────────────────────────────────────
_mongo_client = None
_static_data_cache = {}

_LANG_DB_MAP = {
    "tr": "database_attribute_tr", "tr-TR": "database_attribute_tr",
    "de": "database_attribute_de", "de-DE": "database_attribute_de",
    "ru": "database_attribute_ru", "ru-RU": "database_attribute_ru",
    "ar": "database_attribute_ar", "ar-AR": "database_attribute_ar",
    "en": "database_attribute_en", "en-US": "database_attribute_en",
    "es": "database_attribute_sp", "es-ES": "database_attribute_sp",
    "ja": "database_attribute_jp", "ja-JP": "database_attribute_jp",
    "ko": "database_attribute_ko", "ko-KR": "database_attribute_ko",
}

_STATIC_DOCS = [
    ("eye",      "eyes_distance"),
    ("eye",      "eyes_size"),
    ("eye",      "eyes_compare"),
    ("eyebrow",  "eyebrows_eyes_distance"),
    ("lip",      "lips_width"),
    ("lip",      "lips_thickness"),
    ("lip",      "lips_height_compare"),
    ("nose",     "nose_size"),
    ("nose",     "nose_length"),
    ("nose",     "nose_width"),
    ("forehead", "forehead_distance"),
]

_FIELD_MAP = {
    "tr": "cumle_tr", "tr-TR": "cumle_tr",
    "en": "cumle_en", "en-US": "cumle_en",
    "ko": "cumle_ko", "ko-KR": "cumle_ko",
    "es": "cumle_sp", "es-ES": "cumle_sp",
    "ar": "cumle_ar", "ar-AR": "cumle_ar",
    "ja": "cumle_jp", "ja-JP": "cumle_jp",
    "de": "cumle_de", "de-DE": "cumle_de",
    "ru": "cumle_ru", "ru-RU": "cumle_ru",
}


def _get_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(os.environ.get('MONGO_URI', ""))
    return _mongo_client


def _load_static_data(db_name: str) -> dict:
    global _static_data_cache
    if db_name in _static_data_cache:
        return _static_data_cache[db_name]
    dbref = _get_client()[db_name]
    cache = {}
    for col_name, doc_id in _STATIC_DOCS:
        doc = dbref[col_name].find_one({"_id": doc_id})
        cache[doc_id] = dict(doc) if doc else {}
    _static_data_cache[db_name] = cache
    return cache


def motivate(img, lang):

    result = Cal(img)
    _r0 = _r0; _r1 = _r1; _r2 = _r2; _r3 = _r3; _r4 = _r4

    _base_lang = lang.split('-')[0] if lang else ''
    _lmget = _LANG_DB_MAP.get
    db_name = _lmget(lang, _lmget(_base_lang, "database_attribute_en"))
    static = _load_static_data(db_name)

    sifatlar = []
    for doc_id, category_key in [
        ("eyes_distance",          _r0["eyes_distance"]),
        ("eyes_size",              _r0["eyes_size"]),
        ("eyes_compare",           _r0["eyes_compare"]),
        ("eyebrows_eyes_distance", _r1["eyebrows_eyes_distance"]),
        ("lips_width",             _r2["lips_width"]),
        ("lips_thickness",         _r2["lips_thickness"]),
        ("lips_height_compare",    _r2["lips_height_compare"]),
        ("nose_size",              _r3["nose_size"]),
        ("nose_length",            _r3["nose_length"]),
        ("nose_width",             _r3["nose_width"]),
        ("forehead_distance",      _r4["forehead_distance"]),
    ]:
        sifatlar += list(static.get(doc_id, {}).get(category_key, {}).keys())

    sifatlar = [s for s in sifatlar if s not in ('att1', 'att2')]
    if not sifatlar:
        return ''
    _rc = random.choice
    sifat = _rc(sifatlar)

    client = _get_client()
    mycol = client["facesyma-backend"]["appfaceapi_motivate"]
    _fmget = _FIELD_MAP.get
    field_name = _fmget(lang, _fmget(_base_lang, "cumle_en"))

    sifat_list = [x[field_name] for x in mycol.find({"sifat": sifat}, {"_id": 0, field_name: 1}) if field_name in x]

    if not sifat_list:
        return ''
    return _rc(sifat_list)
