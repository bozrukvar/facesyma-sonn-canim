"""
art_matcher.py
==============
Personality-based art-match engine (no TF/MediaPipe).
  - Personality score: user's sıfatlar → cluster scores vs artwork cluster weights
  - Fallback: total cluster weight ranking (no analysis history needed)
  - Rotation: per-user history in MongoDB (user_art_history)
"""

import random
from datetime import datetime

# Minimum cluster score to include in results
_MIN_SCORE = 0.10

# Grade thresholds
_GRADE_MAP = [(90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (0, "C")]


def _grade(pct: float) -> str:
    for threshold, grade in _GRADE_MAP:
        if pct >= threshold:
            return grade
    return "C"


# ---------------------------------------------------------------------------
# Personality / cluster scoring
# ---------------------------------------------------------------------------

def score_personality(artwork_clusters: dict, user_clusters: dict) -> float:
    if not artwork_clusters or not user_clusters:
        return 0.0
    total_w = sum(artwork_clusters.values())
    if total_w == 0.0:
        return 0.0
    dot = sum(w * user_clusters.get(c, 0.0) for c, w in artwork_clusters.items())
    return min(dot / total_w, 1.0)


def _default_score(artwork_clusters: dict) -> float:
    """When no user history: score by total cluster weight (variety)."""
    total = sum(artwork_clusters.values()) if artwork_clusters else 0
    return min(total / 3.0, 1.0)


# ---------------------------------------------------------------------------
# User sıfatlar → cluster scores from latest analysis_history
# ---------------------------------------------------------------------------

def _get_user_cluster_scores(user_id) -> dict:
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
        sifatlar = doc.get("positive_sifatlar") or doc.get("sifatlar") or []
        return score_from_sifatlar(list(sifatlar)) if sifatlar else {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Rotation helpers
# ---------------------------------------------------------------------------

def _get_shown_ids(user_id, db) -> set:
    hist = db["user_art_history"].find_one(
        {"user_id": user_id}, {"_id": 0, "shown": 1}
    )
    return set(hist.get("shown", [])) if hist else set()


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
# Main entry point — NO TF/MediaPipe
# ---------------------------------------------------------------------------

def match_artworks(
    img_path: str,
    lang: str = "tr",
    user_id=None,
    n: int = 3,
) -> dict:
    """
    Personality-based art match (no TF required).
    Uses user's cluster scores from their latest face analysis history.
    Falls back to cluster-weight ranking if no history.
    """
    # ── 1. Load art pool from MongoDB ──────────────────────────────────────
    db        = None
    pool_docs = []
    try:
        from admin_api.utils.mongo import _get_db
        db        = _get_db()
        pool_docs = list(db["art_pool"].find({}, {"_id": 0}))
    except Exception:
        pass

    if not pool_docs:
        # MongoDB pool not seeded — return empty result with error message
        return {
            "matches": [],
            "best_match": None,
            "overall_score": 0,
            "grade": "C",
            "message": "Art pool not available.",
        }

    # ── 2. Personality cluster scores from analysis history ────────────────
    user_clusters = _get_user_cluster_scores(user_id)
    has_clusters  = bool(user_clusters)

    # ── 3. Score every artwork ─────────────────────────────────────────────
    scored: list[tuple[float, dict]] = []
    for doc in pool_docs:
        if has_clusters:
            sc = score_personality(doc.get("clusters", {}), user_clusters)
        else:
            sc = _default_score(doc.get("clusters", {}))
        if sc >= _MIN_SCORE:
            scored.append((sc, doc))

    if not scored:
        # All scores below threshold — take any top docs
        scored = [(_default_score(d.get("clusters", {})), d) for d in pool_docs]

    scored.sort(key=lambda x: x[0], reverse=True)

    # ── 4. Rotation ────────────────────────────────────────────────────────
    if user_id and db is not None:
        shown_ids = _get_shown_ids(user_id, db)
        unseen = [(sc, doc) for sc, doc in scored if doc["id"] not in shown_ids]
        if not unseen:
            _reset_shown(user_id, db)
            unseen = scored

        pool = unseen[:max(n * 2, 5)]
        chosen = random.sample(pool, min(n, len(pool)))
        chosen.sort(key=lambda x: x[0], reverse=True)

        for _, doc in chosen:
            _mark_shown(user_id, doc["id"], db)

        top_n = chosen
    else:
        top_n = scored[:n]

    # ── 5. Build response ──────────────────────────────────────────────────
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
