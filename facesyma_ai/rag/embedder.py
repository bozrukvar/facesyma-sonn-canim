"""
facesyma_ai/rag/embedder.py
===========================
Embedding generation using Ollama's nomic-embed-text model.

Uses Redis caching to avoid redundant embedding requests.
Cache is shared across all workers and persists across sessions.
Graceful degradation: if Redis unavailable, embeddings regenerated.
"""

import os
import requests
import logging
import hashlib
import pickle
from typing import List
from facesyma_ai.core.redis_client import redis_get, redis_set, redis_clear_pattern

log = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768
EMBEDDING_CACHE_TTL = 86400 * 7  # 7 days


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for text using Ollama nomic-embed-text.

    Checks Redis first for cached embedding (shared across all workers).
    Falls back to calling Ollama if cache miss.
    Caches result to Redis with 7-day TTL.

    Args:
        text: Text to embed

    Returns:
        List of floats representing the embedding (768-dim)

    Raises:
        RuntimeError: If Ollama API fails
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be non-empty string")

    # Generate cache key: SHA256 hash of text (first 32 chars)
    cache_key = f"emb:v1:{hashlib.sha256(text.encode()).hexdigest()[:32]}"

    # Check Redis cache
    cached = redis_get(cache_key)
    if cached:
        try:
            return pickle.loads(cached)
        except Exception as e:
            log.warning(f"Failed to deserialize cached embedding for '{text[:50]}': {e}")
            # Fall through to regenerate

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding", [])

        if not embedding or len(embedding) != EMBEDDING_DIM:
            raise RuntimeError(f"Invalid embedding dimension: expected {EMBEDDING_DIM}, got {len(embedding)}")

        # Cache to Redis for 7 days
        redis_set(cache_key, pickle.dumps(embedding), ttl=EMBEDDING_CACHE_TTL)
        return embedding

    except requests.exceptions.RequestException as e:
        log.error(f"Ollama embedding error: {e}")
        raise RuntimeError(f"Failed to generate embedding: {str(e)}")


def get_embedding_dimension() -> int:
    """Get the embedding dimension (768 for nomic-embed-text)"""
    return EMBEDDING_DIM


def clear_embedding_cache():
    """Clear all cached embeddings from Redis"""
    deleted = redis_clear_pattern("emb:v1:*")
    log.info(f"✓ Cleared {deleted} cached embeddings from Redis")
