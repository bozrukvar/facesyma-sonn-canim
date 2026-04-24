"""
facesyma_ai/core/cache_invalidation.py
======================================
Centralized cache invalidation strategy for all Redis caches.

Problem solved:
  - Embeddings cache: Invalidate when knowledge base docs update
  - Chroma query cache: Invalidate when collection changes
  - LLM response cache: Invalidate when coach modules/sifats change
  - Session cache: Invalidate on logout/password change/expiry
  - Leaderboard cache: Invalidate when coins/badges/missions update

Strategy:
  1. Event-triggered invalidation (CoinService, BadgeService, etc. trigger)
  2. Time-based expiry (TTL handled by Redis)
  3. Pattern-based deletion (clear all embeddings, all LLM responses, etc.)
  4. Graceful degradation (if invalidation fails, cache still works)
"""

import logging
from typing import List, Optional
from enum import Enum
from facesyma_ai.core.redis_client import redis_delete, redis_clear_pattern, get_redis

log = logging.getLogger(__name__)

try:
    from gamification.websocket_events import on_leaderboard_invalidated as _ws_leaderboard_invalidated
except Exception:
    _ws_leaderboard_invalidated = None


class CacheLayer(str, Enum):
    """Cache layer identifiers"""
    EMBEDDINGS = "emb"
    CHROMA_QUERIES = "chroma"
    LLM_RESPONSES = "llm"
    SESSIONS = "session"
    LEADERBOARDS = "lb"


class InvalidationRule:
    """Single invalidation rule"""

    def __init__(
        self,
        cache_layer: CacheLayer,
        pattern: str,
        reason: str,
        critical: bool = False
    ):
        """
        Args:
            cache_layer: Which cache layer to invalidate
            pattern: Redis pattern to match (e.g., "emb:v1:*")
            reason: Human-readable reason for invalidation
            critical: If True, log as ERROR if invalidation fails
        """
        self.cache_layer = cache_layer
        self.pattern = pattern
        self.reason = reason
        self.critical = critical


class CacheInvalidationManager:
    """Central cache invalidation orchestrator"""

    # ════════════════════════════════════════════════════════════════════════════
    # INVALIDATION RULES BY CACHE LAYER
    # ════════════════════════════════════════════════════════════════════════════

    # Embedding cache invalidation rules
    EMBEDDING_RULES = {
        "knowledge_base_update": InvalidationRule(
            CacheLayer.EMBEDDINGS,
            "emb:v1:*",
            "Knowledge base documents updated",
            critical=True
        ),
    }

    # Chroma query cache invalidation rules
    CHROMA_RULES = {
        "collection_update": InvalidationRule(
            CacheLayer.CHROMA_QUERIES,
            "chroma:v1:*",
            "Chroma collection modified",
            critical=False  # Cache will be regenerated on next query
        ),
        "specific_collection": InvalidationRule(
            CacheLayer.CHROMA_QUERIES,
            "chroma:v1:{collection_name}:*",
            "Specific Chroma collection updated"
        ),
    }

    # LLM response cache invalidation rules
    LLM_RULES = {
        "module_update": InvalidationRule(
            CacheLayer.LLM_RESPONSES,
            "llm:v1:*",
            "Coach module descriptions or sifat mapping changed",
            critical=True
        ),
    }

    # Session cache invalidation rules
    SESSION_RULES = {
        "user_logout": InvalidationRule(
            CacheLayer.SESSIONS,
            "session:v1:{session_id}",
            "User logged out"
        ),
        "password_change": InvalidationRule(
            CacheLayer.SESSIONS,
            "session:v1:*",  # Invalidate all for this user? Or just old ones?
            "User password changed"
        ),
    }

    # Leaderboard cache invalidation rules
    LEADERBOARD_RULES = {
        "coin_awarded": InvalidationRule(
            CacheLayer.LEADERBOARDS,
            "lb:*",
            "Coins awarded (affects all leaderboards)",
            critical=False
        ),
        "badge_unlocked": InvalidationRule(
            CacheLayer.LEADERBOARDS,
            "lb:*",
            "Badge unlocked (affects leaderboards)",
            critical=False
        ),
        "mission_completed": InvalidationRule(
            CacheLayer.LEADERBOARDS,
            "lb:*",
            "Mission completed (affects community leaderboards)",
            critical=False
        ),
        "specific_leaderboard": InvalidationRule(
            CacheLayer.LEADERBOARDS,
            "lb:{leaderboard_type}:{trait_id}:{community_id}:*",
            "Specific leaderboard updated"
        ),
    }

    @staticmethod
    def invalidate_embeddings() -> int:
        """Invalidate all embedding cache"""
        return CacheInvalidationManager._execute_invalidation(
            CacheLayer.EMBEDDINGS,
            "emb:v1:*",
            "Knowledge base update"
        )

    @staticmethod
    def invalidate_chroma_cache(collection_name: Optional[str] = None) -> int:
        """
        Invalidate Chroma query cache.

        Args:
            collection_name: If specified, only invalidate this collection

        Returns:
            Number of keys deleted
        """
        if collection_name:
            pattern = f"chroma:v1:{collection_name}:*"
            reason = f"Chroma collection '{collection_name}' updated"
        else:
            pattern = "chroma:v1:*"
            reason = "All Chroma collections updated"

        return CacheInvalidationManager._execute_invalidation(
            CacheLayer.CHROMA_QUERIES,
            pattern,
            reason
        )

    @staticmethod
    def invalidate_llm_cache() -> int:
        """Invalidate all LLM response cache"""
        return CacheInvalidationManager._execute_invalidation(
            CacheLayer.LLM_RESPONSES,
            "llm:v1:*",
            "Coach modules or sifat mapping changed"
        )

    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """
        Invalidate specific session.

        Args:
            session_id: Session to invalidate

        Returns:
            True if deleted, False if not found
        """
        key = f"session:v1:{session_id}"
        result = redis_delete(key)
        if result:
            log.info(f"✓ Invalidated session: {session_id}")
        return result

    @staticmethod
    def invalidate_leaderboards(
        leaderboard_type: Optional[str] = None,
        trait_id: Optional[str] = None,
        community_id: Optional[int] = None
    ) -> int:
        """
        Invalidate leaderboard cache.

        Args:
            leaderboard_type: 'global', 'trait', 'community' or None for all
            trait_id: If leaderboard_type='trait', invalidate specific trait
            community_id: If leaderboard_type='community', invalidate specific community

        Returns:
            Number of keys deleted
        """
        if leaderboard_type == "global":
            pattern = "lb:global:*"
            reason = "Global leaderboard updated"
        elif leaderboard_type == "trait" and trait_id:
            pattern = f"lb:trait:{trait_id}:*"
            reason = f"Trait leaderboard '{trait_id}' updated"
        elif leaderboard_type == "community" and community_id:
            pattern = f"lb:community:{community_id}:*"
            reason = f"Community leaderboard #{community_id} updated"
        else:
            pattern = "lb:*"
            reason = "All leaderboards updated (coins/badges/missions)"

        return CacheInvalidationManager._execute_invalidation(
            CacheLayer.LEADERBOARDS,
            pattern,
            reason,
            critical=False  # Leaderboard cache is non-critical
        )

    @staticmethod
    def _execute_invalidation(
        cache_layer: CacheLayer,
        pattern: str,
        reason: str,
        critical: bool = False
    ) -> int:
        """
        Execute invalidation and log results.

        Args:
            cache_layer: Which cache layer
            pattern: Redis pattern to delete
            reason: Reason for invalidation
            critical: If True, log failure as ERROR

        Returns:
            Number of keys deleted
        """
        _clv = cache_layer.value
        try:
            deleted = redis_clear_pattern(pattern)
            log.info(
                f"✓ Cache invalidated: {_clv} "
                f"(pattern: {pattern}, deleted: {deleted}, reason: {reason})"
            )
            return deleted

        except Exception as e:
            level = log.error if critical else log.warning
            level(
                f"{'✗' if critical else '⚠'} Cache invalidation failed: "
                f"{_clv} (pattern: {pattern}): {e}"
            )
            return 0

    @staticmethod
    def get_cache_stats() -> dict:
        """
        Get Redis cache statistics.

        Returns:
            Dict with cache layer stats
        """
        r = get_redis()
        if not r:
            return {"error": "Redis unavailable"}

        try:
            info = r.info("memory")
            _rdbsize = r.dbsize
            dbsize = _rdbsize()
            _infoget = info.get

            stats = {
                "total_keys": dbsize,
                "memory_used_mb": round(_infoget("used_memory", 0) / 1024 / 1024, 2),
                "memory_max_mb": round(_infoget("maxmemory", 512) / 1024 / 1024, 2),
                "memory_percent": round(
                    (_infoget("used_memory", 0) / max(_infoget("maxmemory", 1), 1)) * 100, 1
                ),
                "evicted_keys": _infoget("evicted_keys", 0),
            }

            # Count keys by layer
            for layer in CacheLayer:
                _lv = layer.value
                count = _rdbsize()  # Rough estimate
                pattern = f"{_lv}:v1:*"
                try:
                    # Count using SCAN to avoid blocking
                    count = sum(1 for _ in r.scan_iter(match=pattern))
                    stats[f"{_lv}_keys"] = count
                except Exception:
                    pass

            return stats

        except Exception as e:
            log.error(f"Failed to get cache stats: {e}")
            return {"error": "Failed to retrieve cache stats."}


# ════════════════════════════════════════════════════════════════════════════════
# INVALIDATION TRIGGERS (to be called from services)
# ════════════════════════════════════════════════════════════════════════════════


def on_coin_awarded(user_id: int) -> None:
    """
    Call this when coins are awarded to a user.
    Invalidates leaderboards where this user's rank changed.
    Broadcasts WebSocket update to all connected clients.
    """
    # Invalidate leaderboards (user's rank may have changed)
    deleted = CacheInvalidationManager.invalidate_leaderboards()
    log.info(f"Coin awarded to user {user_id} → Invalidated {deleted} leaderboard entries")

    # Broadcast WebSocket update
    if _ws_leaderboard_invalidated:
        try:
            _ws_leaderboard_invalidated(reason="coins_awarded")
        except Exception as e:
            log.debug(f"WebSocket broadcast failed (non-critical): {e}")


def on_badge_unlocked(user_id: int, badge_id: str) -> None:
    """
    Call this when a user unlocks a badge.
    Invalidates badge-related leaderboards.
    Broadcasts WebSocket update to all connected clients.
    """
    # Invalidate all leaderboards (badge counts changed)
    deleted = CacheInvalidationManager.invalidate_leaderboards()
    log.info(
        f"Badge '{badge_id}' unlocked for user {user_id} → "
        f"Invalidated {deleted} leaderboard entries"
    )

    # Broadcast WebSocket update
    if _ws_leaderboard_invalidated:
        try:
            _ws_leaderboard_invalidated(reason="badge_unlocked")
        except Exception as e:
            log.debug(f"WebSocket broadcast failed (non-critical): {e}")


def on_knowledge_base_update() -> None:
    """
    Call this when knowledge base documents are updated.
    Invalidates embedding cache and Chroma query cache.
    """
    emb_deleted = CacheInvalidationManager.invalidate_embeddings()
    chroma_deleted = CacheInvalidationManager.invalidate_chroma_cache()
    log.info(
        f"Knowledge base updated → Invalidated "
        f"{emb_deleted} embeddings, {chroma_deleted} Chroma queries"
    )


def on_coach_module_update() -> None:
    """
    Call this when coach modules or sifat descriptions change.
    Invalidates LLM response cache (module descriptions changed).
    """
    deleted = CacheInvalidationManager.invalidate_llm_cache()
    log.info(f"Coach modules updated → Invalidated {deleted} LLM responses")


def on_mission_completed(community_id: Optional[int] = None) -> None:
    """
    Call this when a community mission completes.
    Invalidates community leaderboards.
    Broadcasts WebSocket update to all connected clients.
    """
    _il = CacheInvalidationManager.invalidate_leaderboards
    if community_id:
        deleted = _il(leaderboard_type="community", community_id=community_id)
    else:
        deleted = _il()

    log.info(
        f"Mission completed (community {community_id}) → "
        f"Invalidated {deleted} leaderboard entries"
    )

    # Broadcast WebSocket update
    if _ws_leaderboard_invalidated:
        try:
            _ws_leaderboard_invalidated(
                leaderboard_type="community" if community_id else None,
                community_id=community_id,
                reason="mission_completed"
            )
        except Exception as e:
            log.debug(f"WebSocket broadcast failed (non-critical): {e}")
