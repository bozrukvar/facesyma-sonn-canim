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
from core.redis_client import redis_get, redis_set, redis_clear_pattern

log = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "mxbai-embed-large")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1024"))
EMBEDDING_CACHE_TTL = 86400 * 7  # 7 days
_CACHE_VERSION = "v2"  # v1=nomic, v2=mxbai-embed-large (stable, 1024-dim)


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

    # Generate cache key: SHA256 hash of text — versioned by model
    cache_key = f"emb:{_CACHE_VERSION}:{hashlib.sha256(text.encode()).hexdigest()[:32]}"

    # Check Redis cache
    cached = redis_get(cache_key)
    if cached:
        try:
            return pickle.loads(cached)
        except Exception as e:
            log.warning(f"Failed to deserialize cached embedding for '{text[:50]}': {e}")

    try:
        # Use batch /api/embed endpoint (single text as list for consistency)
        response = requests.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": EMBED_MODEL, "input": text},
            timeout=30,
        )
        response.raise_for_status()
        embeddings = response.json().get("embeddings", [])
        if not embeddings:
            # Fallback: legacy /api/embeddings endpoint
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            embedding = response.json().get("embedding", [])
        else:
            embedding = embeddings[0]

        _emb_len = len(embedding)
        if not embedding or _emb_len != EMBEDDING_DIM:
            raise RuntimeError(f"Invalid embedding dimension: expected {EMBEDDING_DIM}, got {_emb_len}")

        # Cache to Redis for 7 days
        redis_set(cache_key, pickle.dumps(embedding), ttl=EMBEDDING_CACHE_TTL)
        return embedding

    except requests.exceptions.RequestException as e:
        log.error(f"Ollama embedding error: {e}")
        raise RuntimeError("Failed to generate embedding.")


def embed_texts_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a single Ollama API call.

    Significantly faster than calling embed_text() N times.
    Uses Redis cache per-text; only calls Ollama for cache misses.

    Args:
        texts: List of non-empty strings

    Returns:
        List of embeddings (one per input text, same order)

    Raises:
        RuntimeError: If Ollama API fails for uncached texts
    """
    if not texts:
        return []

    results: List[List[float]] = [None] * len(texts)
    uncached_indices: List[int] = []
    uncached_texts: List[str] = []

    # Check cache for each text
    for i, text in enumerate(texts):
        if not text or not isinstance(text, str):
            results[i] = [0.0] * EMBEDDING_DIM
            continue
        cache_key = f"emb:{_CACHE_VERSION}:{hashlib.sha256(text.encode()).hexdigest()[:32]}"
        cached = redis_get(cache_key)
        if cached:
            try:
                results[i] = pickle.loads(cached)
                continue
            except Exception:
                pass
        uncached_indices.append(i)
        uncached_texts.append(text)

    # Batch embed uncached texts
    if uncached_texts:
        batch_ok = False
        if len(uncached_texts) > 1:
            try:
                response = requests.post(
                    f"{OLLAMA_URL}/api/embed",
                    json={"model": EMBED_MODEL, "input": uncached_texts},
                    timeout=max(30, len(uncached_texts) * 5),
                )
                response.raise_for_status()
                batch_embeddings = response.json().get("embeddings", [])
                for idx, emb in zip(uncached_indices, batch_embeddings):
                    text = texts[idx]
                    if len(emb) != EMBEDDING_DIM:
                        raise RuntimeError(f"Bad embedding dim: {len(emb)}")
                    results[idx] = emb
                    cache_key = f"emb:{_CACHE_VERSION}:{hashlib.sha256(text.encode()).hexdigest()[:32]}"
                    redis_set(cache_key, pickle.dumps(emb), ttl=EMBEDDING_CACHE_TTL)
                batch_ok = True
            except (requests.exceptions.RequestException, RuntimeError) as e:
                log.warning(f"Batch embed failed ({e}), falling back to single-text embedding")

        if not batch_ok:
            # Single-text fallback — handles NaN or server errors on specific texts
            for i, orig_idx in enumerate(uncached_indices):
                text = uncached_texts[i]
                try:
                    response = requests.post(
                        f"{OLLAMA_URL}/api/embed",
                        json={"model": EMBED_MODEL, "input": text},
                        timeout=30,
                    )
                    response.raise_for_status()
                    embs = response.json().get("embeddings", [])
                    emb = embs[0] if embs else []
                    if len(emb) != EMBEDDING_DIM:
                        raise RuntimeError(f"Bad embedding dim: {len(emb)}")
                    results[orig_idx] = emb
                    cache_key = f"emb:{_CACHE_VERSION}:{hashlib.sha256(text.encode()).hexdigest()[:32]}"
                    redis_set(cache_key, pickle.dumps(emb), ttl=EMBEDDING_CACHE_TTL)
                except Exception as e:
                    log.warning(f"Single embed failed for text '{text[:50]}': {e} — using zero vector")
                    results[orig_idx] = [0.0] * EMBEDDING_DIM

    return results


def get_embedding_dimension() -> int:
    """Get the embedding dimension (768 for nomic-embed-text)"""
    return EMBEDDING_DIM


def clear_embedding_cache():
    """Clear all cached embeddings from Redis"""
    deleted = redis_clear_pattern("emb:v2:*")
    log.info(f"✓ Cleared {deleted} cached embeddings from Redis")
