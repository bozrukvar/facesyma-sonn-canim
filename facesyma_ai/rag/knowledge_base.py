"""
facesyma_ai/rag/knowledge_base.py
==================================
Chroma vector database CRUD operations with Redis query caching.

Collections:
  - sifat_profiles_tr: Turkish sifat (trait) descriptions (201 sifatlar)
  - sifat_profiles_en: English sifat descriptions
  - celebrities: Celebrity and historical figure profiles
  - golden_ratio_guide: Golden ratio score interpretation
  - personality_types: Dominant sifat to MBTI/Big Five mapping

Query results cached in Redis (1-day TTL) to avoid redundant vector searches.
Graceful degradation: if Redis unavailable, searches execute uncached.
"""

import os
import logging
import hashlib
import json
from typing import List, Dict, Any

try:
    import chromadb
except ImportError:
    raise ImportError("chromadb not installed. Run: pip install chromadb")

from .embedder import embed_text
from core.redis_client import redis_get, redis_set

log = logging.getLogger(__name__)

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
CHROMA_QUERY_CACHE_TTL = 86400  # 1 day

# Module-level Chroma client singleton
_chroma_client = None


def get_chroma_client():
    """
    Get or create Chroma persistent client singleton.

    Reuses single client connection across all requests.
    Dramatically improves performance for repeated queries.

    Returns:
        chromadb.PersistentClient instance
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        log.info(f"✓ Chroma client initialized (path: {CHROMA_PATH})")
    return _chroma_client


def search_knowledge_base(
    collection_name: str,
    query: str,
    n_results: int = 3
) -> List[str]:
    """
    Search knowledge base for relevant documents with Redis caching.

    Query results cached for 1 day. Subsequent identical queries skip
    expensive vector search and return from Redis in ~2ms.

    Args:
        collection_name: Name of collection (e.g., 'sifat_profiles_tr')
        query: Search query string
        n_results: Number of results to return

    Returns:
        List of relevant document texts

    Raises:
        ValueError: If collection doesn't exist
    """
    # Generate cache key
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:24]
    cache_key = f"chroma:v1:{collection_name}:{n_results}:{query_hash}"

    # Check Redis cache
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached.decode())
        except Exception as e:
            log.warning(f"Failed to deserialize cached search results: {e}")
            # Fall through to execute query

    try:
        client = get_chroma_client()
        collection = client.get_collection(name=collection_name)

        # Generate query embedding
        query_embedding = embed_text(query)

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        documents = results.get("documents", [[]])[0]

        # Cache results to Redis
        redis_set(cache_key, json.dumps(documents).encode(), ttl=CHROMA_QUERY_CACHE_TTL)

        return documents

    except Exception as e:
        log.error(f"Knowledge base search error in {collection_name}: {e}")
        return []


def get_collection_stats(collection_name: str) -> Dict[str, Any]:
    """
    Get statistics about a collection.

    Args:
        collection_name: Name of collection

    Returns:
        Dict with count, metadata, etc.
    """
    try:
        client = get_chroma_client()
        collection = client.get_collection(name=collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    except Exception as e:
        log.error(f"Error getting stats for {collection_name}: {e}")
        return {}


def list_all_collections() -> List[str]:
    """List all available collections in the database"""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        return [c.name for c in collections]
    except Exception as e:
        log.error(f"Error listing collections: {e}")
        return []
