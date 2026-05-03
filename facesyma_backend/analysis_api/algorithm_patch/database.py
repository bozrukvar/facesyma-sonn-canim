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
    "bn": "database_attribute_bn", "bn-BD": "database_attribute_bn",
    "fr": "database_attribute_fr", "fr-FR": "database_attribute_fr",
    "hi": "database_attribute_hi", "hi-IN": "database_attribute_hi",
    "id": "database_attribute_id", "id-ID": "database_attribute_id",
    "it": "database_attribute_it", "it-IT": "database_attribute_it",
    "pl": "database_attribute_pl", "pl-PL": "database_attribute_pl",
    "pt": "database_attribute_pt", "pt-BR": "database_attribute_pt", "pt-PT": "database_attribute_pt",
    "ur": "database_attribute_ur", "ur-PK": "database_attribute_ur",
    "vi": "database_attribute_vi", "vi-VN": "database_attribute_vi",
    "zh": "database_attribute_zh", "zh-CN": "database_attribute_zh", "zh-TW": "database_attribute_zh",
}

_STATIC_DOCS = [
    ("eye",       "eyes_distance"),
    ("eye",       "eyes_size"),
    ("eye",       "eyes_compare"),
    ("eyebrow",   "eyebrows_eyes_distance"),
    ("lip",       "lips_width"),
    ("lip",       "lips_thickness"),
    ("lip",       "lips_height_compare"),
    ("nose",      "nose_size"),
    ("nose",      "nose_length"),
    ("nose",      "nose_width"),
    ("forehead",  "forehead_distance"),
    ("jaw",       "jaw"),
    ("cheekbone", "cheekbone"),
    ("chin",      "chin"),
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
    Enhanced analysis pipeline — 3 improvement phases:

    Faz 1 — jaw/cheekbone/chin/symmetry entegrasyonu + face_profile zenginleştirme
             Simetri skoru tüm sıfat güvenlerini modüle eder (yüksek simetri → +güven)

    Faz 2 — Ağırlıklı ölçüm skorlaması
             Gözler (1.4x) > Dudaklar (1.2x) > Burun (1.1x) > Alın (0.8x)
             Her sıfat skoru basit ortalama yerine anatomik önem ağırlığıyla hesaplanır

    Faz 3 — Çoklu ölçüm güven artırımı
             Bir sıfatı N farklı bölge destekliyorsa skor boost alır:
             1 ölçüm → 1.00x | 2 → 1.15x | 3 → 1.25x | 4+ → 1.35x (max 1.0)
    """
    total_att    = {}
    measurements = {}

    # Faz 2: ağırlıklı akümülasyon
    _wsum  = {}   # sifat → weighted score sum
    _wtot  = {}   # sifat → total weight
    # Faz 3: destek sayısı
    _count = {}   # sifat → kaç ölçüm bu sıfatı destekledi

    result = Cal(img)
    db_name    = _lang_to_db(lang)
    static     = _load_static_data(db_name)
    get_values = _get_pos_neg()

    _r0 = result[0]; _r1 = result[1]; _r2 = result[2]; _r3 = result[3]; _r4 = result[4]

    # Faz 2: anatomik önem ağırlıkları
    _WEIGHTS = {
        "eyes_distance":          1.4,
        "eyes_size":              1.3,
        "eyes_compare":           1.0,
        "eyebrows_eyes_distance": 0.9,
        "lips_width":             1.2,
        "lips_thickness":         1.1,
        "lips_height_compare":    1.0,
        "nose_size":              1.1,
        "nose_length":            1.0,
        "nose_width":             1.0,
        "forehead_distance":      0.8,
        "jaw":                    1.0,
        "cheekbone":              1.1,
        "chin":                   0.9,
    }

    # eyes_size_score: r ve l ortalaması (calculator.py'da ayrı tutulur)
    _eyes_size_score = (
        _r0.get("eyes_size_r_score", 0.7) + _r0.get("eyes_size_l_score", 0.7)
    ) / 2

    # Faz 1: yeni bölge ölçümleri — measurement_sections'dan önce hesaplanır
    symmetry_score = 0.75
    symmetry_data  = {}
    jaw_data       = {}
    cheekbone_data = {}
    chin_data      = {}

    try:
        from symmetry import measure_symmetry
        symmetry_data  = measure_symmetry(img)
        symmetry_score = symmetry_data.get("overall_symmetry", 0.75)
    except Exception:
        pass

    try:
        from jaw import measure_jaw
        jaw_data = measure_jaw(img)
    except Exception:
        pass

    try:
        from cheekbone import measure_cheekbone
        cheekbone_data = measure_cheekbone(img)
    except Exception:
        pass

    try:
        from chin import measure_chin
        chin_data = measure_chin(img)
    except Exception:
        pass

    jaw_score  = 0.85 if "golden"   in jaw_data.get("jaw_width_category",  "") else 0.60
    cb_score   = 0.85 if "golden"   in cheekbone_data.get("cheekbone_category", "") else 0.60
    chin_score = 0.85 if "balanced" in chin_data.get("chin_category",       "") else 0.60

    measurement_sections = [
        ("eyes_distance",          _r0["eyes_distance"],          _r0.get("eyes_distance_score",          0.7)),
        ("eyes_size",              _r0["eyes_size"],               _eyes_size_score),
        ("eyes_compare",           _r0["eyes_compare"],            0.7),
        ("eyebrows_eyes_distance", _r1["eyebrows_eyes_distance"],  _r1.get("eyebrows_eyes_distance_score", 0.7)),
        ("lips_width",             _r2["lips_width"],              _r2.get("lips_width_score",             0.7)),
        ("lips_thickness",         _r2["lips_thickness"],          _r2.get("lips_thickness_score",         0.7)),
        ("lips_height_compare",    _r2["lips_height_compare"],     _r2.get("lips_height_score",            0.7)),
        ("nose_size",              _r3["nose_size"],               0.7),
        ("nose_length",            _r3["nose_length"],             _r3.get("nose_length_score",            0.7)),
        ("nose_width",             _r3["nose_width"],              _r3.get("nose_width_score",             0.7)),
        ("forehead_distance",      _r4["forehead_distance"],       _r4.get("forehead_distance_score",      0.7)),
    ]

    # Yeni bölgeler — kategori varsa ölçüm döngüsüne dahil et
    if jaw_data.get("jaw_width_category"):
        measurement_sections.append(("jaw",       jaw_data["jaw_width_category"],         jaw_score))
    if cheekbone_data.get("cheekbone_category"):
        measurement_sections.append(("cheekbone", cheekbone_data["cheekbone_category"],   cb_score))
    if chin_data.get("chin_category"):
        measurement_sections.append(("chin",      chin_data["chin_category"],             chin_score))

    for mname, category, score in measurement_sections:
        try:
            w     = _WEIGHTS.get(mname, 1.0)
            mdict = static.get(mname, {}).get(category, {})
            mlist = list(mdict.keys())

            for sifat in mlist:
                sentences = mdict.get(sifat, [])
                if sentences:
                    total_att[sifat] = random.choice(sentences)
                    # Faz 2: ağırlıklı birikim
                    _wsum[sifat]  = _wsum.get(sifat, 0.0) + score * w
                    _wtot[sifat]  = _wtot.get(sifat, 0.0) + w
                    # Faz 3: destek sayısı
                    _count[sifat] = _count.get(sifat, 0) + 1

            measurements[mname] = {
                "category": category,
                "score":    round(score, 3),
                "weight":   w,
                "sifatlar": mlist,
            }
        except Exception:
            pass

    # Faz 2: ağırlıklı ortalama skoru hesapla
    sifat_scores = {
        s: round(_wsum[s] / _wtot[s], 3)
        for s in _wsum if _wtot.get(s, 0) > 0
    }

    # Faz 3: çoklu ölçüm güven artırımı
    _BOOST = {1: 1.00, 2: 1.15, 3: 1.25}   # 4+ → 1.35x
    for s in list(sifat_scores.keys()):
        mult = _BOOST.get(_count.get(s, 1), 1.35)
        sifat_scores[s] = min(1.0, round(sifat_scores[s] * mult, 3))

    # ── Faz 1: simetri measurements kaydı ───────────────────────────────────
    measurements["symmetry"] = {
        "category": symmetry_data.get("symmetry_category", "unknown"),
        "score":    symmetry_score,
        "weight":   1.5,
        "sifatlar": [],
    }

    # Faz 1: simetri modifikatörü — yüksek simetri tüm skorları biraz artırır
    # sym=0.75 → 1.0x (nötr) | sym=1.0 → ~1.075x | sym=0.50 → ~0.925x
    sym_mod = 1.0 + (symmetry_score - 0.75) * 0.3
    for s in list(sifat_scores.keys()):
        sifat_scores[s] = min(1.0, round(sifat_scores[s] * sym_mod, 3))

    # Çatışma çözümü
    new_att     = Param(list(total_att.keys()))
    new_att_set = set(new_att)

    # Çatışan sıfatları hem sifat_scores'tan hem total_att'tan temizle
    for s in list(sifat_scores.keys()):
        if s not in new_att_set:
            del sifat_scores[s]
    for s in list(total_att.keys()):
        if s not in new_att_set:
            del total_att[s]

    # Kategorize
    _pos = get_values['positive']
    _neg = get_values['negative']
    _unb = get_values['unbiased']
    p  = {k: total_att[k] for k in _pos if k in total_att}
    n  = {k: total_att[k] for k in _neg if k in total_att}
    un = {k: total_att[k] for k in _unb if k in total_att}

    total_final = dict(chain.from_iterable(t.items() for t in (p, n, un)))
    _vals = list(total_final.values())
    character_analysis = ''.join(map(str, random.sample(_vals, len(_vals))))

    # Yüz profili — tüm bölgeler dahil
    base_scores   = list(sifat_scores.values())
    region_scores = []
    if jaw_data:
        region_scores.append(0.85 if "golden" in jaw_data.get("jaw_width_category", "") else 0.60)
    if cheekbone_data:
        region_scores.append(0.85 if "golden" in cheekbone_data.get("cheekbone_category", "") else 0.60)
    if chin_data:
        region_scores.append(0.85 if "balanced" in chin_data.get("chin_category", "") else 0.60)

    combined = base_scores + region_scores
    overall_golden_ratio = round(sum(combined) / len(combined) if combined else 0.7, 3)

    top_sifatlar = [
        {"sifat": s, "score": sc}
        for s, sc in heapq.nlargest(10, sifat_scores.items(), key=itemgetter(1))
    ]

    _pk = list(p.keys()); _nk = list(n.keys()); _unk = list(un.keys())
    return {
        "sifat_scores":     sifat_scores,
        "sifat_categories": {"positive": _pk, "negative": _nk, "unbiased": _unk},
        "face_profile": {
            "overall_symmetry":     symmetry_score,
            "overall_golden_ratio": overall_golden_ratio,
            "key_measurements":     len(measurements),
            "new_regions": {
                "jaw":       jaw_data.get("jaw_width_category",      "N/A"),
                "cheekbone": cheekbone_data.get("cheekbone_category", "N/A"),
                "chin":      chin_data.get("chin_category",           "N/A"),
                "symmetry":  symmetry_data.get("symmetry_category",   "N/A"),
            },
            "symmetry_details": symmetry_data.get("symmetry_details", {}),
        },
        "measurements":      measurements,
        "character_analysis": character_analysis,
        "top_sifatlar":      top_sifatlar,
        "positive_sifatlar": _pk,
        "negative_sifatlar": _nk,
        "unbiased_sifatlar": _unk,
    }
