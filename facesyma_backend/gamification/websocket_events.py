"""
gamification/websocket_events.py
================================
Integration between cache invalidation and WebSocket broadcasting.

When cache is invalidated, broadcasts are sent to all connected WebSocket clients
to trigger real-time leaderboard updates.
"""

import logging
import asyncio
from asgiref.sync import async_to_sync

log = logging.getLogger(__name__)


# Called from cache_invalidation.py when leaderboards are invalidated
def on_leaderboard_invalidated(
    leaderboard_type: str = None,
    trait_id: str = None,
    community_id: int = None,
    reason: str = "cache_invalidated"
):
    """
    Handle leaderboard cache invalidation.

    Broadcasts WebSocket update to all connected clients.

    Called from:
    - facesyma_ai/core/cache_invalidation.py
    - When: Coins awarded, badges unlocked, missions completed

    Args:
        leaderboard_type: 'global', 'trait', 'community', or None for all
        trait_id: Required if leaderboard_type='trait'
        community_id: Required if leaderboard_type='community'
        reason: Why cache was invalidated (coins_awarded, badge_unlocked, etc)
    """
    try:
        from gamification.consumers import broadcast_leaderboard_update

        # If no specific leaderboard type, invalidate all
        if leaderboard_type is None:
            # Broadcast to global
            async_to_sync(broadcast_leaderboard_update)(
                "global",
                reason=reason
            )

            # Note: Broadcasting to all traits and communities would require
            # a list of all trait_ids and community_ids, which is expensive.
            # Instead, clients should refresh when they see a global update.

        elif leaderboard_type == "global":
            async_to_sync(broadcast_leaderboard_update)(
                "global",
                reason=reason
            )

        elif leaderboard_type == "trait":
            async_to_sync(broadcast_leaderboard_update)(
                "trait",
                trait_id=trait_id,
                reason=reason
            )

        elif leaderboard_type == "community":
            async_to_sync(broadcast_leaderboard_update)(
                "community",
                community_id=community_id,
                reason=reason
            )

        log.debug(f"✓ WebSocket broadcast: {leaderboard_type or 'all'} ({reason})")

    except ImportError:
        # Channels not available, skip WebSocket broadcast
        log.debug(f"Channels not available, skipping WebSocket broadcast")

    except Exception as e:
        log.error(f"Error broadcasting leaderboard update: {e}")


# Called when a user's rank changes (after leaderboard recomputation)
def on_user_rank_changed(
    leaderboard_type: str,
    user_id: int,
    username: str,
    old_rank: int,
    new_rank: int,
    coins_gained: int = 0,
    trait_id: str = None,
    community_id: int = None
):
    """
    Handle user rank change.

    Broadcasts WebSocket rank change to all connected clients.

    Called from:
    - Services when computing leaderboard and user rank changes

    Args:
        leaderboard_type: 'global', 'trait', 'community'
        user_id: User's ID
        username: User's username
        old_rank: Previous rank
        new_rank: New rank
        coins_gained: Coins earned
        trait_id: Required if leaderboard_type='trait'
        community_id: Required if leaderboard_type='community'
    """
    try:
        # Only broadcast if rank actually changed
        if old_rank == new_rank:
            return

        from gamification.consumers import broadcast_rank_change

        async_to_sync(broadcast_rank_change)(
            leaderboard_type,
            user_id,
            username,
            old_rank,
            new_rank,
            coins_gained,
            trait_id,
            community_id
        )

        log.debug(
            f"✓ WebSocket rank change: {username} "
            f"({old_rank} → {new_rank}) +{coins_gained} coins"
        )

    except ImportError:
        # Channels not available, skip WebSocket broadcast
        log.debug(f"Channels not available, skipping WebSocket broadcast")

    except Exception as e:
        log.error(f"Error broadcasting rank change: {e}")
