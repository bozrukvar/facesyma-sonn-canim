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


def advisor(img, lang):

    result = Cal(img)
    _r0 = _r0; _r1 = _r1; _r2 = _r2; _r3 = _r3; _r4 = _r4

    _lmget = _LANG_DB_MAP.get
    db_name = _lmget(lang, _lmget(lang.split('-')[0] if lang else '', "database_attribute_en"))
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
    mycol = client["facesyma-backend"]["appfaceapi_advisor"]
    field_name = "cumle_tr" if lang in ("tr", "tr-TR") else "cumle_en"

    sifat_list = [x[field_name] for x in mycol.find({"sifat": sifat}, {"_id": 0, field_name: 1}) if field_name in x]

    if not sifat_list:
        return ''
    return _rc(sifat_list)
