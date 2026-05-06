"""
facesyma_ai/rag/populate_coach_kb.py
======================================
Coach DB (MongoDB) → Chroma vector DB ingest.

Reads all sıfat coaching content from facesyma-coach-backup MongoDB and
embeds it into per-language Chroma collections for RAG retrieval.

Usage:
    # All languages (default: tr + en)
    python populate_coach_kb.py

    # Specific languages
    python populate_coach_kb.py --langs tr en de

    # All 18 languages
    python populate_coach_kb.py --all-langs

    # Clear and rebuild
    python populate_coach_kb.py --clear --langs tr en

    # Stats only
    python populate_coach_kb.py --stats

Environment:
    MONGO_URI  — MongoDB connection string (required)
    OLLAMA_URL — Ollama embedding service URL (default: http://localhost:11434)
    CHROMA_PATH — Chroma DB path (default: ./chroma_db)
"""

import os
import sys
import json
import logging
import argparse
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent dir to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
except ImportError:
    print("ERROR: chromadb not installed. Run: pip install chromadb")
    sys.exit(1)

try:
    from pymongo import MongoClient
except ImportError:
    print("ERROR: pymongo not installed.")
    sys.exit(1)

from rag.embedder import embed_text, embed_texts_batch

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

# ── Config ────────────────────────────────────────────────────────────────────

MONGO_URI   = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
BACKUP_DB   = "facesyma-coach-backup"
CHROMA_PATH = os.environ.get("CHROMA_PATH", str(Path(__file__).parent.parent / "chroma_db"))

# Language collection name map (matches coach_api.py)
_LANG_COL_MAP = {"ja": "jp", "ko": "kr", "es": "sp"}

ALL_LANGS = ["tr", "en", "de", "ru", "ar", "es", "ko", "ja",
             "zh", "hi", "fr", "pt", "bn", "id", "ur", "it", "vi", "pl"]

DEFAULT_LANGS = ["tr", "en"]  # embed these two by default

# The 14 deep coaching modules to embed
COACH_MODULES = [
    # Original 14 modules
    "saglik_esenwlik", "dogruluk_sadakat", "guvenlik", "suc_egilim",
    "iliski_yonetimi", "iletisim_becerileri", "stres_yonetimi", "ozguven",
    "zaman_yonetimi", "kisisel_hedefler", "astroloji_harita", "dogum_analizi",
    "yas_koc_ozet", "vucut_dil",
    # 13 new media/lifestyle modules (patch_media_modules_v1)
    "etkinlik_tavsiye", "spor_aktivite", "kariyer_yolu", "insan_kaynaklari",
    "duygusal_ruhsal", "meditasyon_egzersiz", "kitap_tavsiye", "film_tavsiye",
    "muzik_tavsiye", "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon",
    "saglik_tavsiye",
]

# Also embed these legacy modules if present
LEGACY_MODULES = [
    "kariyer", "liderlik", "duygusal", "uyum", "beceri",
    "ik", "tavsiye", "motivasyon", "etkinlik", "muzik", "film_dizi",
]

MAX_CHUNK_CHARS = 512  # max chars per Chroma document
BATCH_SIZE      = 50   # upsert batch size


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """Split text into chunks of ≤max_chars on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    # Split on '. ' or '\n'
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    chunks: List[str] = []
    buf = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(buf) + len(part) + 1 <= max_chars:
            buf = f"{buf} {part}".strip()
        else:
            if buf:
                chunks.append(buf)
            # If single part is larger than limit, hard-split
            while len(part) > max_chars:
                chunks.append(part[:max_chars])
                part = part[max_chars:]
            buf = part
    if buf:
        chunks.append(buf)
    return chunks or [text[:max_chars]]


def _text_from_value(value: Any) -> str:
    """Extract embeddable text from a module field value."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        # E.g. giyim module: extract text values recursively
        parts = []
        for v in value.values():
            t = _text_from_value(v)
            if t:
                parts.append(t)
        return " | ".join(parts)[:MAX_CHUNK_CHARS * 4]
    if isinstance(value, list):
        parts = [_text_from_value(i) for i in value if i]
        return " | ".join(p for p in parts if p)[:MAX_CHUNK_CHARS * 4]
    return str(value).strip() if value else ""


# ── MongoDB ───────────────────────────────────────────────────────────────────

def get_mongo_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[BACKUP_DB]


def fetch_sifat_docs(lang: str, db) -> List[Dict[str, Any]]:
    """Fetch all sıfat documents from coach_attributes_{lang_col}."""
    lang_col = _LANG_COL_MAP.get(lang, lang)
    col_name = f"coach_attributes_{lang_col}"
    try:
        col = db[col_name]
        docs = list(col.find({}, {m: 1 for m in COACH_MODULES + LEGACY_MODULES + ["_id"]}))
        log.info(f"Fetched {len(docs)} sıfat docs from {col_name}")
        return docs
    except Exception as e:
        log.error(f"MongoDB fetch error for {col_name}: {e}")
        return []


# ── Chroma ────────────────────────────────────────────────────────────────────

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def collection_name(lang: str) -> str:
    return f"coach_content_{lang}"


def get_or_create_collection(client, lang: str):
    return client.get_or_create_collection(
        name=collection_name(lang),
        metadata={"hnsw:space": "cosine"},
    )


def clear_collection(client, lang: str):
    name = collection_name(lang)
    try:
        client.delete_collection(name)
        log.info(f"Cleared collection: {name}")
    except Exception:
        pass


# ── Ingest ────────────────────────────────────────────────────────────────────

def ingest_lang(lang: str, db, chroma_client, clear: bool = False) -> int:
    """
    Embed all coaching content for a language into Chroma.

    Returns number of documents upserted.
    """
    if clear:
        clear_collection(chroma_client, lang)

    docs = fetch_sifat_docs(lang, db)
    if not docs:
        log.warning(f"No documents for lang={lang}, skipping")
        return 0

    collection = get_or_create_collection(chroma_client, lang)
    all_modules = COACH_MODULES + LEGACY_MODULES

    # Collect all chunks first, then batch-embed
    pending_ids:   List[str] = []
    pending_texts: List[str] = []
    pending_metas: List[Dict] = []

    total_upserted = 0
    skipped = 0

    for doc in docs:
        sifat = str(doc.get("_id", ""))
        if not sifat:
            continue

        for module in all_modules:
            raw_value = doc.get(module)
            if not raw_value:
                continue

            full_text = _text_from_value(raw_value)
            if not full_text or len(full_text) < 10:
                skipped += 1
                continue

            chunks = _chunk_text(full_text)
            for i, chunk in enumerate(chunks):
                doc_id = f"{sifat}__{module}" if len(chunks) == 1 else f"{sifat}__{module}__c{i}"
                pending_ids.append(doc_id)
                pending_texts.append(chunk)
                pending_metas.append({
                    "sifat":     sifat,
                    "module":    module,
                    "lang":      lang,
                    "chunk_idx": i,
                })

    # Batch embed and upsert in BATCH_SIZE groups
    total = len(pending_ids)
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_ids   = pending_ids[start:end]
        batch_texts = pending_texts[start:end]
        batch_metas = pending_metas[start:end]

        try:
            batch_embs = embed_texts_batch(batch_texts)
        except RuntimeError as e:
            log.warning(f"Batch embedding failed at {start}: {e}, skipping batch")
            skipped += len(batch_ids)
            continue

        collection.upsert(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=batch_embs,
            metadatas=batch_metas,
        )
        total_upserted += len(batch_ids)
        # Force HNSW index build after each batch (prevents WAL backlog / compaction errors)
        try:
            collection.query(
                query_embeddings=[batch_embs[0]],
                n_results=1,
                include=[],
            )
        except Exception:
            pass  # query failure is OK here; just for WAL flush
        if total > 100:
            log.info(f"  Upserted {total_upserted}/{total} ({lang})")

    log.info(f"✓ {lang}: {total_upserted} docs upserted, {skipped} empty skipped")
    return total_upserted


# ── CLI ───────────────────────────────────────────────────────────────────────

def print_stats(chroma_client):
    print("\n── Coach KB Stats ─────────────────────────────────")
    try:
        cols = chroma_client.list_collections()
        coach_cols = [c for c in cols if c.name.startswith("coach_content_")]
        if not coach_cols:
            print("  No coach_content collections found.")
            return
        for col in sorted(coach_cols, key=lambda c: c.name):
            print(f"  {col.name:30s} {col.count():5d} docs")
    except Exception as e:
        print(f"  Error: {e}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Populate Coach KB in Chroma")
    parser.add_argument("--langs", nargs="+", default=DEFAULT_LANGS,
                        help="Languages to process (default: tr en)")
    parser.add_argument("--all-langs", action="store_true",
                        help="Process all 18 languages")
    parser.add_argument("--clear", action="store_true",
                        help="Clear existing collections before inserting")
    parser.add_argument("--stats", action="store_true",
                        help="Show collection stats and exit")
    args = parser.parse_args()

    chroma_client = get_chroma_client()

    if args.stats:
        print_stats(chroma_client)
        return

    langs = ALL_LANGS if args.all_langs else args.langs

    print(f"\nConnecting to MongoDB: {MONGO_URI[:40]}…")
    try:
        db = get_mongo_db()
        db.command("ping")
        print("✓ MongoDB connected")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        sys.exit(1)

    print(f"Chroma path: {CHROMA_PATH}")
    print(f"Languages:   {langs}")
    print(f"Clear first: {args.clear}")
    print(f"Modules:     {len(COACH_MODULES)} coach + {len(LEGACY_MODULES)} legacy\n")

    t0 = time.time()
    total = 0
    for lang in langs:
        print(f"── Ingesting {lang} ──────────────────────────────────")
        n = ingest_lang(lang, db, chroma_client, clear=args.clear)
        total += n

    elapsed = time.time() - t0
    print(f"\n✓ Done: {total} total docs embedded in {elapsed:.1f}s")
    print_stats(chroma_client)


if __name__ == "__main__":
    main()
