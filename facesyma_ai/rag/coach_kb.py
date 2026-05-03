"""
facesyma_ai/rag/coach_kb.py
============================
Coach DB vector search — Chroma wrapper for coaching content.

Collections (per language):
  coach_content_tr  — Turkish coaching content
  coach_content_en  — English coaching content
  (others created lazily on first populate)

Document schema:
  id:       "{sifat}__{module}"          e.g. "dikkatli__stres_yonetimi"
  text:     Module coaching text (≤512 chars per chunk)
  metadata: {sifat, module, lang, chunk_idx}

Query patterns:
  - By sifat list (metadata filter): retrieve coaching for user's top traits
  - Semantic: full-text query against all docs (no filter)
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional

try:
    import chromadb
except ImportError:
    raise ImportError("chromadb not installed. Run: pip install chromadb")

from .knowledge_base import get_chroma_client
from .embedder import embed_text
from core.redis_client import redis_get, redis_set

log = logging.getLogger(__name__)

COACH_CACHE_TTL = 86400  # 1 day

# The 14 deep coaching modules worth embedding
COACH_MODULES = [
    "saglik_esenwlik", "dogruluk_sadakat", "guvenlik", "suc_egilim",
    "iliski_yonetimi", "iletisim_becerileri", "stres_yonetimi", "ozguven",
    "zaman_yonetimi", "kisisel_hedefler", "astroloji_harita", "dogum_analizi",
    "yas_koc_ozet", "vucut_dil",
]

# Human-readable labels for each module (used in system prompt formatting)
MODULE_LABELS = {
    "saglik_esenwlik":    "Sağlık & Esenlik",
    "dogruluk_sadakat":   "Dürüstlük & Sadakat",
    "guvenlik":           "Güvenlik Profili",
    "suc_egilim":         "Risk & Eğilimler",
    "iliski_yonetimi":    "İlişki Yönetimi",
    "iletisim_becerileri":"İletişim Becerileri",
    "stres_yonetimi":     "Stres Yönetimi",
    "ozguven":            "Öz Güven",
    "zaman_yonetimi":     "Zaman Yönetimi",
    "kisisel_hedefler":   "Kişisel Hedefler",
    "astroloji_harita":   "Astroloji Haritası",
    "dogum_analizi":      "Doğum Analizi",
    "yas_koc_ozet":       "Yaşam Koçu Özeti",
    "vucut_dil":          "Beden Dili",
}

# Module → semantic topic keywords (for relevance scoring in get_coach_context)
MODULE_TOPICS: Dict[str, List[str]] = {
    "saglik_esenwlik":    ["sağlık", "enerji", "fitness", "uyku", "beslenme", "health", "wellness", "energy"],
    "dogruluk_sadakat":   ["güven", "sadakat", "dürüstlük", "trust", "loyalty", "honesty"],
    "guvenlik":           ["güvenlik", "koruma", "risk", "security", "protection", "safety"],
    "suc_egilim":         ["risk", "tehlike", "eğilim", "danger", "tendency"],
    "iliski_yonetimi":    ["ilişki", "aşk", "partner", "aile", "arkadaş", "relationship", "love", "family"],
    "iletisim_becerileri":["iletişim", "konuşma", "dinleme", "empati", "communication", "speech", "listening"],
    "stres_yonetimi":     ["stres", "kaygı", "baskı", "sakinlik", "stress", "anxiety", "pressure", "calm"],
    "ozguven":            ["özgüven", "kendine güven", "özdeğer", "confidence", "self-esteem", "worth"],
    "zaman_yonetimi":     ["zaman", "verimlilik", "disiplin", "planlama", "time", "productivity", "planning"],
    "kisisel_hedefler":   ["hedef", "amaç", "gelecek", "başarı", "goal", "ambition", "future", "success"],
    "astroloji_harita":   ["astroloji", "burç", "gezegen", "astrology", "zodiac", "planet"],
    "dogum_analizi":      ["doğum", "numeroloji", "yaşam yolu", "birth", "numerology", "life path"],
    "yas_koc_ozet":       ["koç", "öğüt", "rehber", "tavsiye", "coach", "advice", "guidance"],
    "vucut_dil":          ["beden dili", "jest", "mimik", "body language", "gesture", "expression"],
}


def _collection_name(lang: str) -> str:
    return f"coach_content_{lang}"


def _cache_key(collection: str, query: str, n: int, sifatlar: List[str]) -> str:
    raw = f"{collection}:{query}:{n}:{','.join(sorted(sifatlar))}"
    return f"coach_rag:v1:{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def get_coach_collection(lang: str):
    """Get or create coach Chroma collection for a language."""
    client = get_chroma_client()
    name = _collection_name(lang)
    try:
        return client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        log.error(f"Failed to get/create collection {name}: {e}")
        return None


def search_coach_content(
    lang: str,
    query: str,
    sifatlar: Optional[List[str]] = None,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Semantic search over coach content for given language.

    Args:
        lang: Language code (tr, en, …)
        query: User message or coaching topic
        sifatlar: Optional list of sifat names to filter by (metadata where clause)
        n_results: Max documents to return

    Returns:
        List of {text, sifat, module, module_label, score} dicts
    """
    if not query:
        return []

    _sifatlar = sifatlar or []
    cache_key = _cache_key(_collection_name(lang), query, n_results, _sifatlar)

    # Redis cache
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached.decode())
        except Exception:
            pass

    try:
        collection = get_coach_collection(lang)
        if not collection or collection.count() == 0:
            log.debug(f"Coach collection {_collection_name(lang)} empty or missing")
            return []

        query_embedding = embed_text(query)

        # Build metadata filter for sifatlar
        where_filter = None
        if _sifatlar:
            if len(_sifatlar) == 1:
                where_filter = {"sifat": {"$eq": _sifatlar[0]}}
            else:
                where_filter = {"sifat": {"$in": _sifatlar[:10]}}

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = collection.query(**kwargs)

        docs      = results.get("documents",  [[]])[0]
        metas     = results.get("metadatas",  [[]])[0]
        distances = results.get("distances",  [[]])[0]

        items = []
        for doc, meta, dist in zip(docs, metas, distances):
            items.append({
                "text":         doc,
                "sifat":        meta.get("sifat", ""),
                "module":       meta.get("module", ""),
                "module_label": MODULE_LABELS.get(meta.get("module", ""), meta.get("module", "")),
                "score":        round(1 - dist, 3),  # cosine similarity
            })

        redis_set(cache_key, json.dumps(items).encode(), ttl=COACH_CACHE_TTL)
        return items

    except Exception as e:
        log.warning(f"Coach content search failed ({lang}): {e}")
        return []


def get_coach_collection_stats(lang: str) -> Dict[str, Any]:
    """Return count and sample info for the coach collection."""
    try:
        col = get_coach_collection(lang)
        if col is None:
            return {"lang": lang, "count": 0, "status": "missing"}
        return {"lang": lang, "count": col.count(), "status": "ok"}
    except Exception as e:
        return {"lang": lang, "count": 0, "status": str(e)}
