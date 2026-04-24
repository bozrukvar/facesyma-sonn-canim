import heapq
import os
import random
from functools import lru_cache
from operator import itemgetter
import numpy as np
from calculator import *
from contrast import *
from pymongo import MongoClient
from itertools import chain
from scorer import get_sifat_score

# ── Module-level cache (survives across analyses in the same process) ──────────
_mongo_client = None
_static_data_cache = {}   # {db_key: {doc_id: dict}}
_pos_neg_cache = None     # pos/neg/unbiased value lists

_LANG_DB_MAP = {
    "tr": "database_attribute_tr", "tr-TR": "database_attribute_tr",
    "de": "database_attribute_de", "de-DE": "database_attribute_de",
    "ru": "database_attribute_ru", "ru-RU": "database_attribute_ru",
    "ar": "database_attribute_ar", "ar-AR": "database_attribute_ar",
    "en": "database_attribute_en", "en-US": "database_attribute_en",
    "es": "database_attribute_sp", "es-ES": "database_attribute_sp",
    "ko": "database_attribute_kr", "ko-KR": "database_attribute_kr",
    "ja": "database_attribute_jp", "ja-JP": "database_attribute_jp",
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
    """Load + cache all static scoring documents for a language database."""
    global _static_data_cache
    if db_name in _static_data_cache:
        return _static_data_cache[db_name]
    client = _get_client()
    dbref = client[db_name]
    cache = {}
    for col_name, doc_id in _STATIC_DOCS:
        doc = dbref[col_name].find_one({"_id": doc_id})
        cache[doc_id] = dict(doc) if doc else {}
    _static_data_cache[db_name] = cache
    return cache


def _get_pos_neg() -> dict:
    """Load + cache the positive/negative/unbiased sifat classification."""
    global _pos_neg_cache
    if _pos_neg_cache is not None:
        return _pos_neg_cache
    doc = _get_client()['pos_neg']['attribute'].find_one(
        {"_id": "values"}, {"_id": 0, "positive": 1, "negative": 1, "unbiased": 1}
    )
    _pos_neg_cache = doc if doc else {'positive': [], 'negative': [], 'unbiased': []}
    return _pos_neg_cache


@lru_cache(maxsize=32)
def _lang_to_db(lang: str) -> str:
    _lmget = _LANG_DB_MAP.get
    return _lmget(lang, _lmget(lang.split('-')[0] if lang else '', "database_attribute_en"))



def databases(img, lang):

    total_att = {}
    result = Cal(img)

    db_name = _lang_to_db(lang)
    static = _load_static_data(db_name)
    _sget = static.get
    get_values = _get_pos_neg()

    _r0 = result[0]; _r1 = result[1]; _r2 = result[2]; _r3 = result[3]; _r4 = result[4]
    _MEASURE_KEYS = [
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
    ]
    _named_texts = {}
    for doc_id, category in _MEASURE_KEYS:
        series = _sget(doc_id, {})
        for sifat, sentences in series.get(category, {}).items():
            if sentences:
                _named_texts[sifat] = random.choice(sentences)

    _ntg = _named_texts.get
    eye_distance_text     = {k: v for k in _sget("eyes_distance",          {}).get(_r0["eyes_distance"],          {}) if (v := _ntg(k)) is not None}
    eye_size_text         = {k: v for k in _sget("eyes_size",               {}).get(_r0["eyes_size"],               {}) if (v := _ntg(k)) is not None}
    eye_compare_text      = {k: v for k in _sget("eyes_compare",            {}).get(_r0["eyes_compare"],            {}) if (v := _ntg(k)) is not None}
    eyebrow_distance_text = {k: v for k in _sget("eyebrows_eyes_distance",  {}).get(_r1["eyebrows_eyes_distance"],  {}) if (v := _ntg(k)) is not None}
    lip_width_text        = {k: v for k in _sget("lips_width",              {}).get(_r2["lips_width"],              {}) if (v := _ntg(k)) is not None}
    lip_thickness_text    = {k: v for k in _sget("lips_thickness",          {}).get(_r2["lips_thickness"],          {}) if (v := _ntg(k)) is not None}
    lip_compare_text      = {k: v for k in _sget("lips_height_compare",     {}).get(_r2["lips_height_compare"],     {}) if (v := _ntg(k)) is not None}
    size_nose_text        = {k: v for k in _sget("nose_size",               {}).get(_r3["nose_size"],               {}) if (v := _ntg(k)) is not None}
    length_nose_text      = {k: v for k in _sget("nose_length",             {}).get(_r3["nose_length"],             {}) if (v := _ntg(k)) is not None}
    width_nose_text       = {k: v for k in _sget("nose_width",              {}).get(_r3["nose_width"],              {}) if (v := _ntg(k)) is not None}
    forehead_distance_text= {k: v for k in _sget("forehead_distance",       {}).get(_r4["forehead_distance"],       {}) if (v := _ntg(k)) is not None}

    _update = total_att.update
    _update(eye_distance_text)
    _update(eye_size_text)
    _update(eye_compare_text)
    _update(eyebrow_distance_text)
    _update(lip_width_text)
    _update(lip_thickness_text)
    _update(lip_compare_text)
    _update(size_nose_text)
    _update(length_nose_text)
    _update(width_nose_text)
    _update(forehead_distance_text)

    _tak = total_att.keys
    new_att = Param(list(_tak()))

    set_difference = _tak() ^ set(new_att)
    list_difference = list(set_difference)

    for m in list_difference:
        del total_att[m]

    p = {k: total_att[k] for k in get_values['positive'] if k in total_att}
    n = {n: total_att[n] for n in get_values['negative'] if n in total_att}
    un = {un: total_att[un] for un in get_values['unbiased'] if un in total_att}

    total_att = dict(chain.from_iterable(t.items() for t in (p, n, un)))

    _vals = list(total_att.values())
    total_text = ''.join(map(str, random.sample(_vals, len(_vals))))
    return total_text


def enhanced_databases(img, lang):
    """
    Enhanced version of databases() that returns structured JSON for Ollama integration.

    Returns dict with:
        - sifat_scores: each sıfat with 0-1 confidence score
        - sifat_categories: positive/negative/unbiased lists
        - face_profile: symmetry, golden ratio adherence
        - measurements: detailed measurement data with scores
        - character_analysis: text output (same as databases())
        - top_sifatlar: highest-scoring sıfatlar
    """
    total_att = {}
    sifat_scores = {}
    measurements = {}

    result = Cal(img)

    db_name = _lang_to_db(lang)
    static = _load_static_data(db_name)
    get_values = _get_pos_neg()

    # Collect measurements with scores
    _r0 = result[0]; _r1 = result[1]; _r2 = result[2]; _r3 = result[3]; _r4 = result[4]
    _r0get = _r0.get; _r2get = _r2.get; _r3get = _r3.get
    measurement_sections = [
        ("eyes_distance",          _r0["eyes_distance"],          _r0get("eyes_distance_score", 0.7)),
        ("eyes_size",              _r0["eyes_size"],               _r0get("eyes_size_score", 0.7)),
        ("eyes_compare",           _r0["eyes_compare"],            0.7),
        ("eyebrows_eyes_distance", _r1["eyebrows_eyes_distance"],  _r1.get("eyebrows_eyes_distance_score", 0.7)),
        ("lips_width",             _r2["lips_width"],              _r2get("lips_width_score", 0.7)),
        ("lips_thickness",         _r2["lips_thickness"],          _r2get("lips_thickness_score", 0.7)),
        ("lips_height_compare",    _r2["lips_height_compare"],     _r2get("lips_height_score", 0.7)),
        ("nose_size",              _r3["nose_size"],               0.7),
        ("nose_length",            _r3["nose_length"],             _r3get("nose_length_score", 0.7)),
        ("nose_width",             _r3["nose_width"],              _r3get("nose_width_score", 0.7)),
        ("forehead_distance",      _r4["forehead_distance"],       _r4.get("forehead_distance_score", 0.7)),
    ]

    # Process each measurement section
    for measurement_name, category, score in measurement_sections:
        try:
            series = static.get(measurement_name, {})
            measurement_dict = series.get(category, {})
            measurement_list = list(measurement_dict.keys())

            for sifat_name in measurement_list:
                sentences = measurement_dict.get(sifat_name, [])
                if sentences:
                    random_sentence = random.choice(sentences)
                    total_att[sifat_name] = random_sentence

                    # Store sıfat score (average of measurement score and existing score)
                    if sifat_name in sifat_scores:
                        _ssn = sifat_scores[sifat_name]
                        sifat_scores[sifat_name] = (_ssn + score) / 2
                    else:
                        sifat_scores[sifat_name] = score

            # Store measurement details
            measurements[measurement_name] = {
                "category": category,
                "score": score,
                "sifatlar": measurement_list
            }
        except Exception as e:
            pass

    # Apply conflict resolution
    new_att = Param(list(total_att.keys()))

    # Remove conflicting sıfatlar from scores dict
    for sifat in list(sifat_scores.keys()):
        if sifat not in new_att:
            del sifat_scores[sifat]

    # Categorize sıfatlar
    p = {k: total_att[k] for k in get_values['positive'] if k in total_att}
    n = {k: total_att[k] for k in get_values['negative'] if k in total_att}
    un = {k: total_att[k] for k in get_values['unbiased'] if k in total_att}

    # Generate character analysis text
    total_att_final = dict(chain.from_iterable(t.items() for t in (p, n, un)))
    _vals = list(total_att_final.values())
    total_text = random.sample(_vals, len(_vals))
    character_analysis = ''.join(map(str, total_text))

    # Calculate face profile stats
    all_scores = list(sifat_scores.values())
    overall_golden_ratio = round(sum(all_scores) / len(all_scores) if all_scores else 0.7, 3)

    # Import symmetry measurement
    try:
        from symmetry import measure_symmetry
        symmetry_data = measure_symmetry(img)
        symmetry_score = symmetry_data.get("overall_symmetry", 0.7)
    except Exception:
        symmetry_score = 0.7

    # Top sıfatlar by score
    top_sifatlar = [{"sifat": s, "score": sc} for s, sc in heapq.nlargest(10, sifat_scores.items(), key=itemgetter(1))]

    _pk = list(p.keys()); _nk = list(n.keys()); _unk = list(un.keys())
    return {
        "sifat_scores": sifat_scores,
        "sifat_categories": {
            "positive": _pk,
            "negative": _nk,
            "unbiased": _unk
        },
        "face_profile": {
            "overall_symmetry": symmetry_score,
            "overall_golden_ratio": overall_golden_ratio,
            "key_measurements": len(measurements)
        },
        "measurements": measurements,
        "character_analysis": character_analysis,
        "top_sifatlar": top_sifatlar,
        "positive_sifatlar": _pk,
        "negative_sifatlar": _nk,
        "unbiased_sifatlar": _unk,
    }
