"""
gamification/consumers.py
========================
WebSocket consumers for real-time leaderboard updates.

Handles:
- User connections to leaderboard rooms
- Broadcasting rank changes
- Integration with cache invalidation
"""

import json
import logging
from datetime import datetime
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

log = logging.getLogger(__name__)


class LeaderboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time leaderboard updates.

    Supports subscription to:
    - Global leaderboard: leaderboard_global
    - Trait-based: leaderboard_trait_{trait_id}
    - Community: leaderboard_community_{community_id}
    """

    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Get leaderboard_type and parameters from URL route
            self.leaderboard_type = self.scope['url_route']['kwargs'].get('leaderboard_type', 'global')
            self.trait_id = self.scope['url_route']['kwargs'].get('trait_id')
            self.community_id = self.scope['url_route']['kwargs'].get('community_id')
            self.user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None

            # Generate room name
            self.room_name = self._generate_room_name()
            self.room_group_name = f"leaderboard_{self.room_name}"

            # Join room
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            log.info(
                f"✓ WebSocket connected: user={self.user_id}, "
                f"leaderboard={self.leaderboard_type}, room={self.room_group_name}"
            )

            # Send initial connection message
            await self.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "leaderboard_type": self.leaderboard_type,
                "trait_id": self.trait_id,
                "community_id": self.community_id,
                "message": f"Connected to {self.leaderboard_type} leaderboard"
            }))

        except Exception as e:
            log.error(f"WebSocket connect error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            log.info(
                f"✓ WebSocket disconnected: user={self.user_id}, "
                f"room={self.room_group_name}, code={close_code}"
            )

        except Exception as e:
            log.error(f"WebSocket disconnect error: {e}")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.

        Supports:
        - {"type": "subscribe"} — Subscribe to updates (default on connect)
        - {"type": "unsubscribe"} — Unsubscribe from updates
        - {"type": "ping"} — Keep-alive ping
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')

            if message_type == 'ping':
                # Respond to ping
                await self.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))

            elif message_type == 'subscribe':
                # Already subscribed by default
                await self.send(json.dumps({
                    "type": "subscribed",
                    "status": "ok",
                    "message": "Subscribed to leaderboard updates"
                }))

            elif message_type == 'unsubscribe':
                # Explicitly unsubscribe
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                await self.send(json.dumps({
                    "type": "unsubscribed",
                    "status": "ok",
                    "message": "Unsubscribed from leaderboard updates"
                }))

            else:
                # Unknown message type
                await self.send(json.dumps({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                }))

        except json.JSONDecodeError:
            await self.send(json.dumps({
                "type": "error",
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            log.error(f"WebSocket receive error: {e}")
            await self.send(json.dumps({
                "type": "error",
                "error": str(e)
            }))

    async def leaderboard_update(self, event):
        """
        Handle leaderboard update broadcast (from cache invalidation handler).

        Called when leaderboard cache is invalidated:
        {
          "type": "leaderboard_update",
          "leaderboard_type": "global",
          "trait_id": null,
          "community_id": null,
          "updated_at": "2026-04-19T14:35:00Z",
          "reason": "coins_awarded"
        }
        """
        try:
            # Forward update to WebSocket client
            await self.send(json.dumps({
                "type": "leaderboard_update",
                "leaderboard_type": event.get("leaderboard_type"),
                "trait_id": event.get("trait_id"),
                "community_id": event.get("community_id"),
                "updated_at": event.get("updated_at"),
                "reason": event.get("reason"),
                "message": "Leaderboard updated, please refresh"
            }))

        except Exception as e:
            log.error(f"Error sending leaderboard update: {e}")

    async def rank_change(self, event):
        """
        Handle user rank change broadcast.

        Called when a specific user's rank changes:
        {
          "type": "rank_change",
          "user_id": 123,
          "username": "ali_expert",
          "old_rank": 50,
          "new_rank": 45,
          "coins_gained": 100,
          "timestamp": "2026-04-19T14:35:00Z"
        }
        """
        try:
            # Forward rank change to WebSocket client
            await self.send(json.dumps({
                "type": "rank_change",
                "user_id": event.get("user_id"),
                "username": event.get("username"),
                "old_rank": event.get("old_rank"),
                "new_rank": event.get("new_rank"),
                "coins_gained": event.get("coins_gained"),
                "timestamp": event.get("timestamp")
            }))

        except Exception as e:
            log.error(f"Error sending rank change: {e}")

    def _generate_room_name(self) -> str:
        """Generate room name from leaderboard parameters"""
        if self.leaderboard_type == 'global':
            return "global"
        elif self.leaderboard_type == 'trait':
            return f"trait_{self.trait_id}"
        elif self.leaderboard_type == 'community':
            return f"community_{self.community_id}"
        else:
            return "global"


# Helper function to broadcast leaderboard updates
async def broadcast_leaderboard_update(
    leaderboard_type: str,
    trait_id: str = None,
    community_id: int = None,
    reason: str = "cache_invalidated"
):
    """
    Broadcast leaderboard update to all connected clients.

    Called from cache invalidation handlers.

    Args:
        leaderboard_type: 'global', 'trait', 'community'
        trait_id: Required if leaderboard_type='trait'
        community_id: Required if leaderboard_type='community'
        reason: Why cache was invalidated (coins_awarded, badge_unlocked, etc)
    """
    try:
        channel_layer = get_channel_layer()

        # Generate room name
        if leaderboard_type == 'global':
            room_name = "global"
        elif leaderboard_type == 'trait':
            room_name = f"trait_{trait_id}"
        elif leaderboard_type == 'community':
            room_name = f"community_{community_id}"
        else:
            return

        room_group_name = f"leaderboard_{room_name}"

        # Broadcast update
        await channel_layer.group_send(
            room_group_name,
            {
                "type": "leaderboard_update",
                "leaderboard_type": leaderboard_type,
                "trait_id": trait_id,
                "community_id": community_id,
                "updated_at": datetime.utcnow().isoformat(),
                "reason": reason
            }
        )

        log.debug(f"✓ Broadcasted leaderboard update: {room_group_name} ({reason})")

    except Exception as e:
        log.error(f"Error broadcasting leaderboard update: {e}")


# Helper function to broadcast rank changes
async def broadcast_rank_change(
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
    Broadcast rank change for a specific user.

    Called when a user's rank changes after coin award/badge unlock.

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
        channel_layer = get_channel_layer()

        # Generate room name
        if leaderboard_type == 'global':
            room_name = "global"
        elif leaderboard_type == 'trait':
            room_name = f"trait_{trait_id}"
        elif leaderboard_type == 'community':
            room_name = f"community_{community_id}"
        else:
            return

        room_group_name = f"leaderboard_{room_name}"

        # Broadcast rank change
        await channel_layer.group_send(
            room_group_name,
            {
                "type": "rank_change",
                "user_id": user_id,
                "username": username,
                "old_rank": old_rank,
                "new_rank": new_rank,
                "coins_gained": coins_gained,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        log.debug(f"✓ Broadcasted rank change: {username} ({old_rank} → {new_rank})")

    except Exception as e:
        log.error(f"Error broadcasting rank change: {e}")
