"""
art_matcher.py
==============
Dual-scoring art-match engine.
  - Geometry score  (Cal() proportions vs artwork's ideal values)
  - Personality score (sıfatlar → cluster scores vs artwork cluster weights)
  - Blend: 40% geo + 60% personality (or 100% whichever side is available)
"""

from collections import defaultdict
import math
import random
from datetime import datetime

# Geometry dimension weights (must sum to 1.0)
_GEO_WEIGHTS = {"jaw_width": 0.35, "face_len_ratio": 0.40, "eye_distance": 0.25}
_GEO_TOLERANCE = 0.20   # ±20% of the ideal value → score drops to 0

# Minimum cluster score to include in results
_MIN_SCORE = 0.15

# Blend weight constants
_W_GEO  = 0.40
_W_PERS = 0.60

# Grade thresholds
_GRADE_MAP = [(90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (0, "C")]


def _grade(pct: float) -> str:
    for threshold, grade in _GRADE_MAP:
        if pct >= threshold:
            return grade
    return "C"


# ---------------------------------------------------------------------------
# Geometry scoring
# ---------------------------------------------------------------------------

def score_geometry(artwork_geo: dict, user_geo: dict) -> float:
    """
    Compare user's face proportions to artwork's ideal values.
    Uses a triangle (linear) decay: full score at ideal, 0 at ±tolerance.
    Returns 0.0–1.0.
    """
    if not artwork_geo or not user_geo:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for dim, w in _GEO_WEIGHTS.items():
        ideal = artwork_geo.get(dim)
        actual = user_geo.get(dim)
        if ideal is None or actual is None:
            continue
        tol = ideal * _GEO_TOLERANCE or 0.1
        diff = abs(actual - ideal)
        dim_score = max(0.0, 1.0 - (diff / tol))
        weighted_sum += dim_score * w
        total_weight += w

    if total_weight == 0.0:
        return 0.0
    return weighted_sum / total_weight


# ---------------------------------------------------------------------------
# Personality / cluster scoring (same dot-product as archetype_mapper)
# ---------------------------------------------------------------------------

def score_personality(artwork_clusters: dict, user_clusters: dict) -> float:
    """
    Weighted dot-product similarity between artwork cluster profile and user's
    cluster scores. Returns 0.0–1.0.
    """
    if not artwork_clusters or not user_clusters:
        return 0.0
    total_w = sum(artwork_clusters.values())
    if total_w == 0.0:
        return 0.0
    dot = sum(w * user_clusters.get(c, 0.0) for c, w in artwork_clusters.items())
    return min(dot / total_w, 1.0)


# ---------------------------------------------------------------------------
# Score blending
# ---------------------------------------------------------------------------

def blend_scores(
    geo_score: float,
    pers_score: float,
    has_portrait: bool,
    has_sifatlar: bool,
) -> float:
    """
    40 % geo + 60 % personality.
    Falls back to available side when one is missing:
      - non-portrait → 100 % personality
      - no sıfatlar  → 100 % geometry (if portrait) else 0
    """
    if not has_portrait and not has_sifatlar:
        return 0.0
    if not has_portrait:
        return pers_score
    if not has_sifatlar:
        return geo_score
    return geo_score * _W_GEO + pers_score * _W_PERS


# ---------------------------------------------------------------------------
# User sıfatlar → cluster scores (from latest analysis_history)
# ---------------------------------------------------------------------------

def _get_user_cluster_scores(user_id) -> dict:
    """
    Fetch the user's latest face-analysis sıfatlar from MongoDB and convert
    them to cluster scores via SIFAT_CLUSTER_MAP.  Returns {} on any failure.
    """
    if not user_id:
        return {}
    try:
        from admin_api.utils.mongo import _get_db
        from archetype_mapper import score_from_sifatlar
        db = _get_db()
        doc = db["analysis_history"].find_one(
            {"user_id": user_id},
            {"positive_sifatlar": 1, "sifatlar": 1},
            sort=[("created_at", -1)],
        )
        if not doc:
            return {}
        # support both field names used across collection versions
        sifatlar = doc.get("positive_sifatlar") or doc.get("sifatlar") or []
        if not sifatlar:
            return {}
        return score_from_sifatlar(list(sifatlar))
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Rotation / history helpers  (same pattern as archetype_mapper)
# ---------------------------------------------------------------------------

def _get_shown_ids(user_id, db) -> set:
    hist = db["user_art_history"].find_one(
        {"user_id": user_id}, {"_id": 0, "shown": 1}
    )
    if not hist:
        return set()
    return set(hist.get("shown", []))


def _mark_shown(user_id, artwork_id: str, db) -> None:
    db["user_art_history"].update_one(
        {"user_id": user_id},
        {"$addToSet": {"shown": artwork_id}, "$set": {"updated_at": datetime.utcnow()}},
        upsert=True,
    )


def _reset_shown(user_id, db) -> None:
    db["user_art_history"].update_one(
        {"user_id": user_id},
        {"$set": {"shown": [], "updated_at": datetime.utcnow()}},
        upsert=True,
    )


# ---------------------------------------------------------------------------
# Primary cluster detection
# ---------------------------------------------------------------------------

def _primary_cluster(clusters: dict) -> str:
    if not clusters:
        return ""
    return max(clusters, key=lambda k: clusters[k])


# ---------------------------------------------------------------------------
# Localisation helpers
# ---------------------------------------------------------------------------

_MATCH_MSG: dict[str, str] = {
    "tr": "Yüzünüz {title} adlı eseri en çok çağrıştırıyor.",
    "en": "Your face most resembles the artwork \"{title}\".",
    "de": "Ihr Gesicht erinnert am meisten an das Kunstwerk \"{title}\".",
    "ru": "Ваше лицо больше всего напоминает произведение «{title}».",
    "ar": "وجهك يشبه أكثر ما يشبه العمل الفني \"{title}\".",
    "es": "Tu rostro se parece más a la obra de arte \"{title}\".",
    "ko": "당신의 얼굴은 \"{title}\" 작품과 가장 닮았습니다.",
    "ja": "あなたの顔は「{title}」という作品に最も似ています。",
    "zh": "您的面孔最像艺术作品《{title}》。",
    "hi": "आपका चेहरा सबसे ज्यादा \"{title}\" कलाकृति से मिलता-जुलता है।",
    "fr": "Votre visage ressemble le plus à l'œuvre d'art \"{title}\".",
    "pt": "Seu rosto se parece mais com a obra de arte \"{title}\".",
    "bn": "আপনার মুখ \"{title}\" শিল্পকর্মের সাথে সবচেয়ে মিল।",
    "id": "Wajah Anda paling mirip dengan karya seni \"{title}\".",
    "ur": "آپ کا چہرہ سب سے زیادہ \"{title}\" شاہکار سے مشابہ ہے۔",
    "it": "Il tuo viso somiglia di più all'opera d'arte \"{title}\".",
    "vi": "Khuôn mặt của bạn giống nhất với tác phẩm nghệ thuật \"{title}\".",
    "pl": "Twoja twarz najbardziej przypomina dzieło sztuki \"{title}\".",
}


def _localise_artwork(doc: dict, lang: str) -> dict:
    """Return display-ready artwork dict in the requested language."""
    _l = lang if lang in ("tr", "en") else "en"

    def _pick(tr_key, en_key, fallback=""):
        return doc.get(f"{tr_key}_{lang}") or doc.get(f"{en_key}_{lang}") \
               or doc.get(f"{tr_key}_{_l}") or doc.get(f"{en_key}_{_l}") or fallback

    title  = doc.get(f"title_{lang}") or doc.get("title_en") or doc.get("title_tr", "")
    artist = doc.get(f"artist_{lang}") or doc.get("artist_en") or doc.get("artist_tr", "")
    museum = doc.get(f"museum_{lang}") or doc.get("museum_en") or doc.get("museum_tr", "")
    style  = doc.get(f"style_{lang}") or doc.get("style_en") or doc.get("style_tr", "")
    reason = doc.get(f"reason_{lang}") or doc.get("reason_en") or doc.get("reason_tr", "")

    return {
        "id":              doc["id"],
        "title":           title,
        "artist":          artist,
        "year":            doc.get("year", ""),
        "museum":          museum,
        "style":           style,
        "reason":          reason,
        "emoji":           doc.get("emoji", "🖼"),
        "image_url":       doc.get("image_url", ""),
        "primary_cluster": _primary_cluster(doc.get("clusters", {})),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def match_artworks(
    img_path: str,
    lang: str = "tr",
    user_id=None,
    n: int = 3,
) -> dict:
    """
    Dual-scoring art match.

    1. Run Cal(img_path) for geometric measurements.
    2. Fetch user's sıfatlar → cluster scores from MongoDB.
    3. Score all artworks: blend(geo, personality).
    4. Apply rotation (skip already-seen, reset when pool exhausted).
    5. Return top-N with localised names, image_url, reason, primary_cluster.

    Falls back gracefully to geometry-only if user has no sıfatlar history,
    or personality-only for non-portrait artworks.
    """
    # ── 1. Geometric measurements ──────────────────────────────────────────
    user_geo: dict = {}
    try:
        from calculator import Cal
        raw = Cal(img_path)
        user_geo = {
            "jaw_width":      raw.get("Jaw",  {}).get("jaw_width_ratio",   1.0),
            "face_len_ratio": raw.get("Nose", {}).get("face_length_ratio", 1.45),
            "eye_distance":   raw.get("Eye",  {}).get("eyes_distance",     1.0),
        }
    except Exception:
        pass

    has_geo = bool(user_geo)

    # ── 2. Personality cluster scores ──────────────────────────────────────
    user_clusters = _get_user_cluster_scores(user_id)
    has_clusters  = bool(user_clusters)

    # ── 3. Load art pool from MongoDB ──────────────────────────────────────
    db        = None
    pool_docs = []
    try:
        from admin_api.utils.mongo import _get_db
        db        = _get_db()
        pool_docs = list(db["art_pool"].find({}, {"_id": 0}))
    except Exception:
        pass

    if not pool_docs:
        # MongoDB pool not seeded — fall back to legacy art_match
        from art_match import match_artwork as _legacy
        return _legacy(img_path, lang=lang)

    # ── 4. Score every artwork ─────────────────────────────────────────────
    scored: list[tuple[float, dict]] = []
    for doc in pool_docs:
        hp = doc.get("has_portrait", False)

        geo_sc  = score_geometry(doc.get("geo", {}), user_geo) if (hp and has_geo) else 0.0
        pers_sc = score_personality(doc.get("clusters", {}), user_clusters) if has_clusters else 0.0

        final = blend_scores(geo_sc, pers_sc, hp, has_clusters)
        if final >= _MIN_SCORE:
            scored.append((final, doc))

    if not scored:
        from art_match import match_artwork as _legacy
        return _legacy(img_path, lang=lang)

    scored.sort(key=lambda x: x[0], reverse=True)

    # ── 5. Rotation (only when user is authenticated) ──────────────────────
    if user_id and db is not None:
        shown_ids = _get_shown_ids(user_id, db)
        unseen = [(sc, doc) for sc, doc in scored if doc["id"] not in shown_ids]
        if not unseen:
            _reset_shown(user_id, db)
            unseen = scored

        # Pick from top-5 for variety
        pool = unseen[:max(n * 2, 5)]
        chosen = random.sample(pool, min(n, len(pool)))
        chosen.sort(key=lambda x: x[0], reverse=True)

        for _, doc in chosen:
            _mark_shown(user_id, doc["id"], db)

        top_n = chosen
    else:
        top_n = scored[:n]

    # ── 6. Build response ──────────────────────────────────────────────────
    _lang = lang if lang in _MATCH_MSG else "en"

    matches = []
    for rank, (score_f, doc) in enumerate(top_n, 1):
        entry = _localise_artwork(doc, _lang)
        entry["rank"]       = rank
        entry["similarity"] = round(score_f * 100, 1)
        matches.append(entry)

    best      = matches[0] if matches else None
    top_score = best["similarity"] if best else 50.0
    msg_title = best["title"] if best else ""

    return {
        "matches":       matches,
        "best_match":    best,
        "overall_score": round(top_score, 1),
        "grade":         _grade(top_score),
        "message":       _MATCH_MSG.get(_lang, _MATCH_MSG["en"]).format(title=msg_title),
    }
