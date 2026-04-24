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
import jwt
from datetime import datetime
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.conf import settings

_JWT_SECRET: str = settings.JWT_SECRET

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
            _scope = self.scope
            _kwargs = _scope['url_route']['kwargs']
            _kget = _kwargs.get
            self.leaderboard_type = _kget('leaderboard_type', 'global')
            _lt = self.leaderboard_type
            self.trait_id = _kget('trait_id')
            self.community_id = _kget('community_id')
            qs = parse_qs(_scope.get('query_string', b'').decode())
            token = (qs.get('token') or [''])[0]
            self.user_id = None
            if token:
                try:
                    payload = jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])
                    self.user_id = payload.get('user_id')
                except Exception:
                    log.warning('LeaderboardWS rejected: invalid/expired token')
                    await self.close(code=4401)
                    return

            # Generate room name
            self.room_name = self._generate_room_name()
            self.room_group_name = f"leaderboard_{self.room_name}"
            _rgn = self.room_group_name

            # Join room
            await self.channel_layer.group_add(
                _rgn,
                self.channel_name
            )

            await self.accept()

            log.info(
                f"✓ WebSocket connected: user={self.user_id}, "
                f"leaderboard={_lt}, room={_rgn}"
            )

            # Send initial connection message
            await self.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "leaderboard_type": _lt,
                "trait_id": self.trait_id,
                "community_id": self.community_id,
                "message": f"Connected to {_lt} leaderboard"
            }))

        except Exception as e:
            log.error(f"WebSocket connect error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Leave room group
            _rgn = self.room_group_name
            await self.channel_layer.group_discard(
                _rgn,
                self.channel_name
            )

            log.info(
                f"✓ WebSocket disconnected: user={self.user_id}, "
                f"room={_rgn}, code={close_code}"
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
        _send = self.send
        _jdumps = json.dumps
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'ping')

            if message_type == 'ping':
                # Respond to ping
                await _send(_jdumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))

            elif message_type == 'subscribe':
                # Already subscribed by default
                await _send(_jdumps({
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
                await _send(_jdumps({
                    "type": "unsubscribed",
                    "status": "ok",
                    "message": "Unsubscribed from leaderboard updates"
                }))

            else:
                # Unknown message type
                await _send(_jdumps({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                }))

        except json.JSONDecodeError:
            await _send(_jdumps({
                "type": "error",
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            log.error(f"WebSocket receive error: {e}")
            await _send(_jdumps({
                "type": "error",
                "error": "An error occurred processing your request."
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
            _eget = event.get
            # Forward update to WebSocket client
            await self.send(json.dumps({
                "type": "leaderboard_update",
                "leaderboard_type": _eget("leaderboard_type"),
                "trait_id": _eget("trait_id"),
                "community_id": _eget("community_id"),
                "updated_at": _eget("updated_at"),
                "reason": _eget("reason"),
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
            _eget = event.get
            # Forward rank change to WebSocket client
            await self.send(json.dumps({
                "type": "rank_change",
                "user_id": _eget("user_id"),
                "username": _eget("username"),
                "old_rank": _eget("old_rank"),
                "new_rank": _eget("new_rank"),
                "coins_gained": _eget("coins_gained"),
                "timestamp": _eget("timestamp")
            }))

        except Exception as e:
            log.error(f"Error sending rank change: {e}")

    def _generate_room_name(self) -> str:
        """Generate room name from leaderboard parameters"""
        _lt = self.leaderboard_type
        if _lt == 'global':
            return "global"
        elif _lt == 'trait':
            return f"trait_{self.trait_id}"
        elif _lt == 'community':
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
