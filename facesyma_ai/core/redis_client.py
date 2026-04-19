"""
facesyma_ai/core/redis_client.py
=================================
Merkezi Redis Client Singleton

Tüm AI modülü tarafından kullanılan merkezi Redis client'ı.
process-wide caching, embedding cache, LLM response cache vb. için.

Graceful degradation: Redis down olunca None döner,
sistem caching olmadan çalışmaya devam eder.

Kullanım:
    from facesyma_ai.core.redis_client import redis_get, redis_set

    # Embedding cache
    cached = redis_get("emb:v1:hash123")
    if cached:
        embedding = pickle.loads(cached)
    else:
        embedding = generate_embedding(text)
        redis_set("emb:v1:hash123", pickle.dumps(embedding), ttl=86400)
"""

import os
import logging
import redis
from typing import Optional

log = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """
    Get shared Redis client singleton.

    Returns None if Redis is unavailable, allowing graceful degradation.
    Never raise exceptions — caching failures should not crash the app.

    Returns:
        redis.Redis instance or None if Redis is down
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=False,  # raw bytes for pickle serialization
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Verify connection
            _redis_client.ping()
            log.info(f"✓ Redis connected: {REDIS_URL}")
        except Exception as e:
            log.warning(f"⚠ Redis unavailable ({REDIS_URL}): {e}. Caching disabled.")
            _redis_client = None  # Mark as unavailable but don't crash

    return _redis_client


def redis_get(key: str) -> Optional[bytes]:
    """
    Get value from Redis.

    Args:
        key: Cache key

    Returns:
        Bytes value or None if not found / Redis unavailable
    """
    r = get_redis()
    if r is None:
        return None

    try:
        return r.get(key)
    except Exception as e:
        log.debug(f"Redis GET failed for key '{key}': {e}")
        return None


def redis_set(key: str, value: bytes, ttl: int = 3600):
    """
    Set value in Redis with optional TTL.

    Args:
        key: Cache key
        value: Bytes to cache
        ttl: Time to live in seconds (default 1 hour)
    """
    r = get_redis()
    if r is None:
        return

    try:
        r.set(key, value, ex=ttl)
    except Exception as e:
        log.debug(f"Redis SET failed for key '{key}': {e}")


def redis_delete(key: str) -> bool:
    """
    Delete key from Redis.

    Args:
        key: Cache key

    Returns:
        True if deleted, False if key not found or Redis unavailable
    """
    r = get_redis()
    if r is None:
        return False

    try:
        return r.delete(key) > 0
    except Exception as e:
        log.debug(f"Redis DELETE failed for key '{key}': {e}")
        return False


def redis_exists(key: str) -> bool:
    """
    Check if key exists in Redis.

    Args:
        key: Cache key

    Returns:
        True if key exists, False if not found or Redis unavailable
    """
    r = get_redis()
    if r is None:
        return False

    try:
        return r.exists(key) > 0
    except Exception as e:
        log.debug(f"Redis EXISTS failed for key '{key}': {e}")
        return False


def redis_clear_pattern(pattern: str) -> int:
    """
    Clear all keys matching a pattern.

    Args:
        pattern: Key pattern (e.g., "emb:v1:*")

    Returns:
        Number of keys deleted
    """
    r = get_redis()
    if r is None:
        return 0

    try:
        # Use SCAN to avoid blocking
        deleted = 0
        for key in r.scan_iter(match=pattern):
            deleted += r.delete(key)
        return deleted
    except Exception as e:
        log.debug(f"Redis CLEAR_PATTERN failed for pattern '{pattern}': {e}")
        return 0


def redis_flush_db():
    """Clear entire Redis database. Use with caution!"""
    r = get_redis()
    if r is None:
        return

    try:
        r.flushdb()
        log.info("✓ Redis database flushed")
    except Exception as e:
        log.warning(f"Redis FLUSHDB failed: {e}")
