"""
facesyma_ai/chat_service/context_enricher.py
============================================
Faz 3 — Kullanıcının güncel durumunu MongoDB'den çekip
sistem promptuna enjekte edilecek kısa bir metin döndürür.

fetch_user_context(user_id, lang, db) → str  (boş string if nothing found)
"""

import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

# ── Dil etiketleri (TR/EN; diğerleri EN fallback) ─────────────────────────────
_L = {
    "tr": {
        "section":    "## Kullanıcı Profili (Güncel)",
        "tests":      "🧠 Testler",
        "archetype":  "🎭 Son arketip eşleşmesi",
        "diet":       "🍽 Beslenme takibi",
        "gamif":      "🎮 Gamification",
        "active":     "aktif",
        "meal_unit":  "öğün",
        "days":       "günde",
        "coin":       "coin",
        "badge":      "rozet",
        "mission":    "aktif görev",
    },
    "en": {
        "section":    "## User Profile (Live)",
        "tests":      "🧠 Assessments",
        "archetype":  "🎭 Last archetype match",
        "diet":       "🍽 Meal tracking",
        "gamif":      "🎮 Gamification",
        "active":     "active",
        "meal_unit":  "meals",
        "days":       "in last 7d",
        "coin":       "coins",
        "badge":      "badges",
        "mission":    "active mission",
    },
}

# Human-readable test names (TR/EN)
_TEST_NAMES = {
    "tr": {
        "personality": "Kişilik",
        "career":      "Kariyer",
        "skills":      "Beceriler",
        "hr":          "İK",
        "relationship": "İlişki",
        "vocation":    "Meslek",
        "attachment":  "Bağlanma",
        "leadership":  "Liderlik",
        "eq":          "Duygusal Zeka",
    },
    "en": {
        "personality": "Personality",
        "career":      "Career",
        "skills":      "Skills",
        "hr":          "HR",
        "relationship": "Relationship",
        "vocation":    "Vocation",
        "attachment":  "Attachment",
        "leadership":  "Leadership",
        "eq":          "EQ",
    },
}

# Archetype type labels
_TYPE_LABELS = {
    "tr": {"celebrity": "Meşhur", "animal": "Hayvan", "plant": "Bitki", "object": "Eşya"},
    "en": {"celebrity": "Celebrity", "animal": "Animal", "plant": "Plant", "object": "Object"},
}


def _lbl(lang: str) -> dict:
    return _L.get(lang, _L["en"])


def _test_name(lang: str, test_type: str) -> str:
    return _TEST_NAMES.get(lang, _TEST_NAMES["en"]).get(test_type, test_type)


def _type_label(lang: str, atype: str) -> str:
    return _TYPE_LABELS.get(lang, _TYPE_LABELS["en"]).get(atype, atype)


# ── Section builders ──────────────────────────────────────────────────────────

def _build_assessment_section(user_id: int, lang: str, db) -> str:
    """Latest assessment results → compact string.  Example:
    Kişilik → açıklık:0.82, dürüstlük:0.74 | Kariyer → analitik:0.9
    """
    try:
        cursor = db["assessment_results"].find(
            {"user_id": user_id},
            {"_id": 0, "test_type": 1, "overall_score": 1, "breakdown": 1, "created_at": 1},
        ).sort("created_at", -1).limit(20)

        # Keep latest per test_type
        latest: dict[str, dict] = {}
        for doc in cursor:
            tt = doc.get("test_type", "")
            if tt and tt not in latest:
                latest[tt] = doc

        if not latest:
            return ""

        parts = []
        for tt, doc in list(latest.items())[:5]:  # max 5 tests
            overall = doc.get("overall_score")
            breakdown = doc.get("breakdown") or {}
            # Top-3 breakdown scores
            if breakdown:
                top3 = sorted(breakdown.items(), key=lambda x: float(x[1] or 0), reverse=True)[:3]
                scores = ", ".join(f"{k}:{float(v):.2f}" for k, v in top3)
            elif overall is not None:
                scores = f"overall:{float(overall):.2f}"
            else:
                continue
            name = _test_name(lang, tt)
            parts.append(f"{name} → {scores}")

        if not parts:
            return ""
        lbl = _lbl(lang)
        return f"{lbl['tests']}: {' | '.join(parts)}"
    except Exception as e:
        log.debug(f"Assessment section failed: {e}")
        return ""


def _build_archetype_section(user_id: int, lang: str, db) -> str:
    """Last shown archetypes per category → compact string."""
    try:
        hist = db["user_archetype_history"].find_one(
            {"user_id": user_id},
            {"_id": 0, "celebrity_shown": 1, "animal_shown": 1,
             "plant_shown": 1, "object_shown": 1},
        )
        if not hist:
            return ""

        # Get last shown ID per type
        last_ids: dict[str, str] = {}
        for atype in ("celebrity", "animal", "plant", "object"):
            shown_list = hist.get(f"{atype}_shown", [])
            if shown_list:
                last_ids[atype] = shown_list[-1]

        if not last_ids:
            return ""

        # Fetch archetype docs
        arch_docs = list(db["archetype_pool"].find(
            {"id": {"$in": list(last_ids.values())}},
            {"_id": 0, "id": 1, "type": 1, "name": 1, "emoji": 1},
        ))
        id_to_doc = {d["id"]: d for d in arch_docs}

        parts = []
        for atype in ("celebrity", "animal", "plant", "object"):
            aid = last_ids.get(atype)
            if not aid:
                continue
            doc = id_to_doc.get(aid)
            if not doc:
                continue
            name_map = doc.get("name", {})
            name = name_map.get(lang) or name_map.get("en") or name_map.get("tr", aid)
            emoji = doc.get("emoji", "")
            tl = _type_label(lang, atype)
            parts.append(f"{name} {emoji} ({tl})")

        if not parts:
            return ""
        lbl = _lbl(lang)
        return f"{lbl['archetype']}: {', '.join(parts)}"
    except Exception as e:
        log.debug(f"Archetype section failed: {e}")
        return ""


def _build_diet_section(user_id: int, lang: str, db) -> str:
    """Meal tracking activity in last 7 days → compact string."""
    try:
        since = (datetime.utcnow() - timedelta(days=7)).isoformat()
        count = db["meal_selections"].count_documents({
            "user_id": user_id,
            "selected_at": {"$gte": since},
        })
        if count == 0:
            return ""
        lbl = _lbl(lang)
        return f"{lbl['diet']}: {count} {lbl['meal_unit']} ({lbl['days']}) — {lbl['active']}"
    except Exception as e:
        log.debug(f"Diet section failed: {e}")
        return ""


def _build_gamif_section(user_id: int, lang: str, db) -> str:
    """Coins, badges, active missions → compact string."""
    try:
        parts = []
        lbl = _lbl(lang)

        # Latest coin balance
        tx = db["coin_transactions"].find_one(
            {"user_id": user_id},
            {"balance_after": 1},
            sort=[("created_at", -1)],
        )
        if tx and tx.get("balance_after") is not None:
            parts.append(f"{int(tx['balance_after'])} {lbl['coin']}")

        # Badge count
        badge_count = db["user_badges"].count_documents({"user_id": user_id})
        if badge_count > 0:
            parts.append(f"{badge_count} {lbl['badge']}")

        # Active community missions
        active_missions = db["community_missions"].count_documents({
            "participants.user_id": user_id,
            "status": "active",
        })
        if active_missions > 0:
            parts.append(f"{active_missions} {lbl['mission']}")

        if not parts:
            return ""
        return f"{lbl['gamif']}: {', '.join(parts)}"
    except Exception as e:
        log.debug(f"Gamif section failed: {e}")
        return ""


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_user_context(user_id: int, lang: str, db) -> str:
    """
    Returns a compact multi-line string describing the user's live state.
    Returns empty string if nothing is available (no user, empty DB, etc.).
    """
    if not user_id:
        return ""

    _lang = lang if lang in _L else "en"
    lbl = _lbl(_lang)

    sections = []
    for builder in (
        _build_assessment_section,
        _build_archetype_section,
        _build_diet_section,
        _build_gamif_section,
    ):
        try:
            result = builder(user_id, _lang, db)
            if result:
                sections.append(result)
        except Exception as e:
            log.debug(f"Context builder {builder.__name__} failed: {e}")

    if not sections:
        return ""

    return lbl["section"] + "\n" + "\n".join(sections)
