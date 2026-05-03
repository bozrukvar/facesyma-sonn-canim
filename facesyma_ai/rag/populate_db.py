"""
facesyma_ai/rag/populate_db.py
==============================
Populate Chroma vector database with knowledge base data.

Usage:
    python populate_db.py              # Load all collections
    python populate_db.py --collection sifat_characteristics_tr  # Load specific collection
    python populate_db.py --clear      # Clear all collections first

Collections to load:
    1. sifat_profiles_tr: 201 Turkish sifat descriptions
    2. sifat_profiles_en: 201 English sifat descriptions
    3. sifat_characteristics_tr: 201 sifatlar × 30+ characteristic sentences (Turkish)
    4. sifat_characteristics_en: 201 sifatlar × 30+ characteristic sentences (English)
    5. celebrities: Celebrity and historical figure profiles
    6. golden_ratio_guide: Golden ratio score interpretation ranges
    7. personality_types: Dominant sifat to MBTI/Big Five mapping
"""

import os
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent dir so 'core' package is importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: chromadb not installed. Run: pip install chromadb")
    sys.exit(1)

from rag.embedder import embed_text, embed_texts_batch

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

_DEFAULT_CHROMA_PATH = str(Path(__file__).parent.parent / "chroma_db")
CHROMA_PATH = os.environ.get("CHROMA_PATH", _DEFAULT_CHROMA_PATH)
DATA_PATH = Path(__file__).parent / "data"


def get_chroma_client():
    """Get Chroma client"""
    return chromadb.PersistentClient(path=CHROMA_PATH)


def load_json_file(filename: str) -> Dict[str, Any]:
    """Load JSON data file"""
    filepath = DATA_PATH / filename
    if not filepath.exists():
        log.warning(f"Data file not found: {filepath}")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def populate_sifat_profiles(lang: str = "tr"):
    """
    Load sifat (trait) profiles into Chroma.

    Each sifat is stored as a document with description.
    """
    _info = log.info
    _info(f"Loading sifat_profiles_{lang}...")

    data = load_json_file(f"sifat_profiles_{lang}.json")
    if not data:
        log.warning(f"No data for sifat_profiles_{lang}")
        return

    client = get_chroma_client()
    collection_name = f"sifat_profiles_{lang}"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        _info(f"  → Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Sifat profiles in {lang}"}
    )

    # Collect then batch-embed
    sifatlar = data.get("sifatlar", [])
    total = len(sifatlar)

    ids, docs, metas = [], [], []
    for idx, sifat in enumerate(sifatlar, 1):
        _sget = sifat.get
        sifat_name = _sget("name", f"sifat_{idx}")
        description = _sget("description", "")
        if not description:
            continue
        ids.append(sifat_name)
        docs.append(description)
        metas.append({"sifat": sifat_name, "lang": lang, "type": "sifat_profile"})

    BATCH = 50
    for start in range(0, len(ids), BATCH):
        b_ids  = ids[start:start+BATCH]
        b_docs = docs[start:start+BATCH]
        b_meta = metas[start:start+BATCH]
        embs = embed_texts_batch(b_docs)
        collection.add(ids=b_ids, documents=b_docs, embeddings=embs, metadatas=b_meta)
        try:
            collection.query(query_embeddings=[embs[0]], n_results=1, include=[])
        except Exception:
            pass
        _info(f"  → Processed {min(start+BATCH, len(ids))}/{len(ids)} sifatlar...")

    _info(f"✓ Loaded {total} sifat profiles into {collection_name}")


def populate_celebrities():
    """Load celebrity and historical figure profiles"""
    _info = log.info
    _info("Loading celebrities...")

    data = load_json_file("celebrities.json")
    if not data:
        log.warning("No data for celebrities")
        return

    client = get_chroma_client()
    collection_name = "celebrities"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        _info(f"  → Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Celebrity and historical figure profiles"}
    )

    # Collect then batch-embed
    profiles = data.get("profiles", [])
    total = len(profiles)

    ids, docs, metas = [], [], []
    for idx, profile in enumerate(profiles, 1):
        _pget = profile.get
        name = _pget("name", f"profile_{idx}")
        description = _pget("description", "")
        if not description:
            descs = _pget("descriptions", {})
            if isinstance(descs, dict):
                description = descs.get("en") or descs.get("tr") or next(iter(descs.values()), "")
            else:
                description = str(descs)
        if not description:
            continue
        ids.append(name)
        docs.append(description)
        metas.append({"name": name, "category": _pget("category", "celebrity"), "type": "celebrity_profile"})

    embs = embed_texts_batch(docs)
    collection.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
    _info(f"✓ Loaded {total} celebrity profiles")


def populate_golden_ratio_guide():
    """Load golden ratio score interpretation ranges"""
    _info = log.info
    _info("Loading golden_ratio_guide...")

    data = load_json_file("golden_ratio_guide.json")
    if not data:
        log.warning("No data for golden_ratio_guide")
        return

    client = get_chroma_client()
    collection_name = "golden_ratio_guide"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        _info(f"  → Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Golden ratio score interpretations"}
    )

    # Collect then batch-embed
    ranges = data.get("ranges", [])
    total = len(ranges)

    ids, docs, metas = [], [], []
    for idx, range_item in enumerate(ranges, 1):
        _riget = range_item.get
        descriptions   = _riget("descriptions", {})
        interpretations = _riget("interpretations", {})
        description  = " | ".join(v for v in descriptions.values() if v) if isinstance(descriptions, dict) else str(descriptions)
        interp_text  = " | ".join(v for v in interpretations.values() if v) if isinstance(interpretations, dict) else str(interpretations)
        full_text = f"{interp_text} {description}".strip()
        if not full_text:
            continue
        ids.append(f"ratio_{idx}")
        docs.append(full_text)
        metas.append({
            "min": _riget("min", 0),
            "max": _riget("max", 1),
            "interpretation_en": interpretations.get("en", "") if isinstance(interpretations, dict) else "",
            "interpretation_tr": interpretations.get("tr", "") if isinstance(interpretations, dict) else "",
            "type": "golden_ratio_range"
        })

    embs = embed_texts_batch(docs)
    collection.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
    _info(f"✓ Loaded {total} golden ratio ranges")


def populate_personality_types():
    """Load personality type mappings (sifat -> MBTI/Big Five)"""
    _info = log.info
    _info("Loading personality_types...")

    data = load_json_file("personality_types.json")
    if not data:
        log.warning("No data for personality_types")
        return

    client = get_chroma_client()
    collection_name = "personality_types"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        _info(f"  → Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Sifat to personality type mappings"}
    )

    # Collect then batch-embed
    mappings = data.get("personality_types", data.get("mappings", []))
    total = len(mappings)

    ids, docs, metas = [], [], []
    for idx, mapping in enumerate(mappings, 1):
        _mapget = mapping.get
        sifat = _mapget("sifat_tr", _mapget("sifat", f"sifat_{idx}"))
        description = _mapget("description", "")
        if not description:
            continue
        ids.append(sifat)
        docs.append(description)
        metas.append({
            "sifat": sifat,
            "sifat_en": _mapget("sifat_en", sifat),
            "mbti": _mapget("mbti", "") if isinstance(_mapget("mbti", ""), str) else str(_mapget("mbti", "")),
            "big_five": json.dumps(_mapget("big_five", ""), ensure_ascii=False) if isinstance(_mapget("big_five", ""), dict) else str(_mapget("big_five", "")),
            "type": "personality_mapping"
        })

    BATCH = 50
    for start in range(0, len(ids), BATCH):
        b_ids  = ids[start:start+BATCH]
        b_docs = docs[start:start+BATCH]
        b_meta = metas[start:start+BATCH]
        embs = embed_texts_batch(b_docs)
        collection.add(ids=b_ids, documents=b_docs, embeddings=embs, metadatas=b_meta)
        try:
            collection.query(query_embeddings=[embs[0]], n_results=1, include=[])
        except Exception:
            pass
        _info(f"  → Processed {min(start+BATCH, len(ids))}/{len(ids)} mappings...")

    _info(f"✓ Loaded {total} personality type mappings")


def populate_sifat_characteristics(lang: str = "tr"):
    """
    Load sifat characteristic sentences into Chroma.

    Each sentence from each sifat is stored as a separate document
    for semantic search capability.

    Args:
        lang: Language code (tr or en)
    """
    _info = log.info
    _info(f"Loading sifat_characteristics_{lang}...")

    data = load_json_file(f"sifat_characteristics_{lang}.json")
    if not data:
        log.warning(f"No data for sifat_characteristics_{lang}")
        return

    client = get_chroma_client()
    collection_name = f"sifat_characteristics_{lang}"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        _info(f"  → Deleted existing collection: {collection_name}")
    except Exception:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Sifat characteristic sentences in {lang}"}
    )

    # Collect all sentences then batch-embed in chunks of 50
    sifatlar = data.get("sifatlar", [])
    total_sifatlar = len(sifatlar)

    ids, docs, metas = [], [], []
    for sifat_idx, sifat in enumerate(sifatlar, 1):
        _sget = sifat.get
        sifat_name = _sget("name", f"sifat_{sifat_idx}")
        for sentence_no, sentence in enumerate(_sget("cumleler", []), 1):
            if not sentence or not isinstance(sentence, str):
                continue
            ids.append(f"{sifat_name}_{sentence_no}")
            docs.append(sentence)
            metas.append({"sifat": sifat_name, "lang": lang, "sentence_no": sentence_no, "type": "characteristic"})

    total_documents = len(ids)
    BATCH = 50
    for start in range(0, total_documents, BATCH):
        b_ids  = ids[start:start+BATCH]
        b_docs = docs[start:start+BATCH]
        b_meta = metas[start:start+BATCH]
        embs = embed_texts_batch(b_docs)
        collection.add(ids=b_ids, documents=b_docs, embeddings=embs, metadatas=b_meta)
        try:
            collection.query(query_embeddings=[embs[0]], n_results=1, include=[])
        except Exception:
            pass
        if start % 500 == 0:
            _info(f"  → Embedded {min(start+BATCH, total_documents)}/{total_documents} sentences...")

    _info(f"✓ Loaded {total_sifatlar} sifatlar with {total_documents} characteristic sentences into {collection_name}")


def clear_all_collections():
    """Clear all collections from the database"""
    client = get_chroma_client()
    collections = client.list_collections()

    for collection in collections:
        _cn = collection.name
        try:
            client.delete_collection(name=_cn)
            log.info(f"✓ Deleted collection: {_cn}")
        except Exception as e:
            log.error(f"Error deleting {_cn}: {e}")


def main():
    _info = log.info
    parser = argparse.ArgumentParser(description="Populate Chroma vector database")
    _addarg = parser.add_argument
    _addarg(
        "--collection",
        type=str,
        help="Load specific collection only"
    )
    _addarg(
        "--clear",
        action="store_true",
        help="Clear all collections before loading"
    )
    _addarg(
        "--lang",
        type=str,
        default="tr",
        help="Language for sifat profiles (tr or en)"
    )

    args = parser.parse_args()

    # Create data directory if it doesn't exist
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    _info(f"Chroma database path: {CHROMA_PATH}")

    if args.clear:
        _info("Clearing all collections...")
        clear_all_collections()

    # Load specific collection or all
    _col = args.collection
    if _col:
        if _col == "sifat_profiles_tr":
            populate_sifat_profiles("tr")
        elif _col == "sifat_profiles_en":
            populate_sifat_profiles("en")
        elif _col == "sifat_characteristics_tr":
            populate_sifat_characteristics("tr")
        elif _col == "sifat_characteristics_en":
            populate_sifat_characteristics("en")
        elif _col == "celebrities":
            populate_celebrities()
        elif _col == "golden_ratio_guide":
            populate_golden_ratio_guide()
        elif _col == "personality_types":
            populate_personality_types()
        else:
            log.error(f"Unknown collection: {_col}")
    else:
        # Load all
        _info("Loading all collections...")
        populate_sifat_profiles("tr")
        populate_sifat_profiles("en")
        populate_sifat_characteristics("tr")
        populate_sifat_characteristics("en")
        populate_celebrities()
        populate_golden_ratio_guide()
        populate_personality_types()

    _info("✓ Database population complete!")


if __name__ == "__main__":
    main()
