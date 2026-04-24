import os
import random
import numpy as np
from calculator import *
from contrast import *
from pymongo import MongoClient
from itertools import chain

# ── Module-level cache ────────────────────────────────────────────────────────
_mongo_client = None
_static_cache = None
_pos_neg_cache = None

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


def _load_static():
    global _static_cache
    if _static_cache is not None:
        return _static_cache
    dbref = _get_client()['database_attribute_en']
    cache = {}
    for col_name, doc_id in _STATIC_DOCS:
        doc = dbref[col_name].find_one({"_id": doc_id})
        cache[doc_id] = dict(doc) if doc else {}
    _static_cache = cache
    return cache


def _get_pos_neg():
    global _pos_neg_cache
    if _pos_neg_cache is not None:
        return _pos_neg_cache
    doc = _get_client()['pos_neg']['attribute'].find_one(
        {"_id": "values"}, {"_id": 0, "positive": 1, "negative": 1, "unbiased": 1}
    )
    _pos_neg_cache = doc if doc else {'positive': [], 'negative': [], 'unbiased': []}
    return _pos_neg_cache


def databases(img):

    total_att = {}
    result = Cal(img)

    static = _load_static()
    _sget = static.get
    get_values = _get_pos_neg()

    _r0 = _r0; _r1 = _r1; _r2 = _r2; _r3 = _r3; _r4 = _r4
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
    total_text = random.sample(_vals, len(_vals))
    total_text = ''.join(map(str, total_text))
    result_text = {"attribute": result, "text": total_text}
    return result_text
