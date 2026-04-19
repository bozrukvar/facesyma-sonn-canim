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

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: chromadb not installed. Run: pip install chromadb")
    sys.exit(1)

from embedder import embed_text

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
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
    log.info(f"Loading sifat_profiles_{lang}...")

    data = load_json_file(f"sifat_profiles_{lang}.json")
    if not data:
        log.warning(f"No data for sifat_profiles_{lang}")
        return

    client = get_chroma_client()
    collection_name = f"sifat_profiles_{lang}"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        log.info(f"  → Deleted existing collection: {collection_name}")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Sifat profiles in {lang}"}
    )

    # Add sifatlar
    sifatlar = data.get("sifatlar", [])
    total = len(sifatlar)

    for idx, sifat in enumerate(sifatlar, 1):
        try:
            sifat_name = sifat.get("name", f"sifat_{idx}")
            description = sifat.get("description", "")

            if not description:
                continue

            # Generate embedding
            embedding = embed_text(description)

            # Add to collection
            collection.add(
                ids=[sifat_name],
                documents=[description],
                embeddings=[embedding],
                metadatas=[{
                    "sifat": sifat_name,
                    "lang": lang,
                    "type": "sifat_profile"
                }]
            )

            if idx % 50 == 0:
                log.info(f"  → Processed {idx}/{total} sifatlar...")

        except Exception as e:
            log.error(f"Error processing sifat {sifat_name}: {e}")

    log.info(f"✓ Loaded {total} sifat profiles into {collection_name}")


def populate_celebrities():
    """Load celebrity and historical figure profiles"""
    log.info("Loading celebrities...")

    data = load_json_file("celebrities.json")
    if not data:
        log.warning("No data for celebrities")
        return

    client = get_chroma_client()
    collection_name = "celebrities"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        log.info(f"  → Deleted existing collection: {collection_name}")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Celebrity and historical figure profiles"}
    )

    # Add profiles
    profiles = data.get("profiles", [])
    total = len(profiles)

    for idx, profile in enumerate(profiles, 1):
        try:
            name = profile.get("name", f"profile_{idx}")
            description = profile.get("description", "")

            if not description:
                continue

            embedding = embed_text(description)

            collection.add(
                ids=[name],
                documents=[description],
                embeddings=[embedding],
                metadatas=[{
                    "name": name,
                    "category": profile.get("category", "celebrity"),
                    "type": "celebrity_profile"
                }]
            )

            if idx % 10 == 0:
                log.info(f"  → Processed {idx}/{total} profiles...")

        except Exception as e:
            log.error(f"Error processing {name}: {e}")

    log.info(f"✓ Loaded {total} celebrity profiles")


def populate_golden_ratio_guide():
    """Load golden ratio score interpretation ranges"""
    log.info("Loading golden_ratio_guide...")

    data = load_json_file("golden_ratio_guide.json")
    if not data:
        log.warning("No data for golden_ratio_guide")
        return

    client = get_chroma_client()
    collection_name = "golden_ratio_guide"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        log.info(f"  → Deleted existing collection: {collection_name}")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Golden ratio score interpretations"}
    )

    # Add ranges
    ranges = data.get("ranges", [])
    total = len(ranges)

    for idx, range_item in enumerate(ranges, 1):
        try:
            range_id = f"ratio_{idx}"
            description = range_item.get("description", "")

            if not description:
                continue

            embedding = embed_text(description)

            collection.add(
                ids=[range_id],
                documents=[description],
                embeddings=[embedding],
                metadatas=[{
                    "min": range_item.get("min", 0),
                    "max": range_item.get("max", 1),
                    "interpretation": range_item.get("interpretation", ""),
                    "type": "golden_ratio_range"
                }]
            )

        except Exception as e:
            log.error(f"Error processing golden ratio range: {e}")

    log.info(f"✓ Loaded {total} golden ratio ranges")


def populate_personality_types():
    """Load personality type mappings (sifat -> MBTI/Big Five)"""
    log.info("Loading personality_types...")

    data = load_json_file("personality_types.json")
    if not data:
        log.warning("No data for personality_types")
        return

    client = get_chroma_client()
    collection_name = "personality_types"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        log.info(f"  → Deleted existing collection: {collection_name}")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Sifat to personality type mappings"}
    )

    # Add mappings
    mappings = data.get("mappings", [])
    total = len(mappings)

    for idx, mapping in enumerate(mappings, 1):
        try:
            sifat = mapping.get("sifat", f"sifat_{idx}")
            description = mapping.get("description", "")

            if not description:
                continue

            embedding = embed_text(description)

            collection.add(
                ids=[sifat],
                documents=[description],
                embeddings=[embedding],
                metadatas=[{
                    "sifat": sifat,
                    "mbti": mapping.get("mbti", ""),
                    "big_five": mapping.get("big_five", ""),
                    "type": "personality_mapping"
                }]
            )

            if idx % 50 == 0:
                log.info(f"  → Processed {idx}/{total} mappings...")

        except Exception as e:
            log.error(f"Error processing {sifat}: {e}")

    log.info(f"✓ Loaded {total} personality type mappings")


def populate_sifat_characteristics(lang: str = "tr"):
    """
    Load sifat characteristic sentences into Chroma.

    Each sentence from each sifat is stored as a separate document
    for semantic search capability.

    Args:
        lang: Language code (tr or en)
    """
    log.info(f"Loading sifat_characteristics_{lang}...")

    data = load_json_file(f"sifat_characteristics_{lang}.json")
    if not data:
        log.warning(f"No data for sifat_characteristics_{lang}")
        return

    client = get_chroma_client()
    collection_name = f"sifat_characteristics_{lang}"

    # Delete existing collection if present
    try:
        client.delete_collection(name=collection_name)
        log.info(f"  → Deleted existing collection: {collection_name}")
    except:
        pass

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Sifat characteristic sentences in {lang}"}
    )

    # Add sifatlar with their sentences
    sifatlar = data.get("sifatlar", [])
    total_sifatlar = len(sifatlar)
    total_documents = 0

    for sifat_idx, sifat in enumerate(sifatlar, 1):
        try:
            sifat_name = sifat.get("name", f"sifat_{sifat_idx}")
            cumleler = sifat.get("cumleler", [])

            # Each sentence is a separate document for semantic search
            for sentence_no, sentence in enumerate(cumleler, 1):
                if not sentence or not isinstance(sentence, str):
                    continue

                doc_id = f"{sifat_name}_{sentence_no}"
                embedding = embed_text(sentence)

                collection.add(
                    ids=[doc_id],
                    documents=[sentence],
                    embeddings=[embedding],
                    metadatas=[{
                        "sifat": sifat_name,
                        "lang": lang,
                        "sentence_no": sentence_no,
                        "type": "characteristic"
                    }]
                )
                total_documents += 1

            if sifat_idx % 50 == 0:
                log.info(f"  → Processed {sifat_idx}/{total_sifatlar} sifatlar...")

        except Exception as e:
            log.error(f"Error processing sifat {sifat_name}: {e}")

    log.info(f"✓ Loaded {total_sifatlar} sifatlar with {total_documents} characteristic sentences into {collection_name}")


def clear_all_collections():
    """Clear all collections from the database"""
    client = get_chroma_client()
    collections = client.list_collections()

    for collection in collections:
        try:
            client.delete_collection(name=collection.name)
            log.info(f"✓ Deleted collection: {collection.name}")
        except Exception as e:
            log.error(f"Error deleting {collection.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Populate Chroma vector database")
    parser.add_argument(
        "--collection",
        type=str,
        help="Load specific collection only"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all collections before loading"
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="tr",
        help="Language for sifat profiles (tr or en)"
    )

    args = parser.parse_args()

    # Create data directory if it doesn't exist
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    log.info(f"Chroma database path: {CHROMA_PATH}")

    if args.clear:
        log.info("Clearing all collections...")
        clear_all_collections()

    # Load specific collection or all
    if args.collection:
        if args.collection == "sifat_profiles_tr":
            populate_sifat_profiles("tr")
        elif args.collection == "sifat_profiles_en":
            populate_sifat_profiles("en")
        elif args.collection == "sifat_characteristics_tr":
            populate_sifat_characteristics("tr")
        elif args.collection == "sifat_characteristics_en":
            populate_sifat_characteristics("en")
        elif args.collection == "celebrities":
            populate_celebrities()
        elif args.collection == "golden_ratio_guide":
            populate_golden_ratio_guide()
        elif args.collection == "personality_types":
            populate_personality_types()
        else:
            log.error(f"Unknown collection: {args.collection}")
    else:
        # Load all
        log.info("Loading all collections...")
        populate_sifat_profiles("tr")
        populate_sifat_profiles("en")
        populate_sifat_characteristics("tr")
        populate_sifat_characteristics("en")
        populate_celebrities()
        populate_golden_ratio_guide()
        populate_personality_types()

    log.info("✓ Database population complete!")


if __name__ == "__main__":
    main()
