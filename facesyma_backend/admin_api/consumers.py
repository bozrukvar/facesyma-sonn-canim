"""
admin_api/consumers.py
======================
WebSocket consumer for real-time admin dashboard updates.

Broadcast helpers allow sync views to push events to connected admin clients.
"""

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import json
import logging

log = logging.getLogger(__name__)


class AdminLiveConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live admin dashboard."""

    GROUP_NAME = 'admin_live'

    async def connect(self):
        """Add consumer to broadcast group."""
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        log.debug(f'Admin WS client connected: {self.channel_name}')

    async def disconnect(self, close_code):
        """Remove consumer from broadcast group."""
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        log.debug(f'Admin WS client disconnected: {self.channel_name}')

    # ── Event handlers (receive from group_send) ────────────────────────────────

    async def stat_update(self, event):
        """Broadcast: KPI/stat update."""
        await self.send(text_data=json.dumps({
            'type': 'stat_update',
            'data': event['data']
        }))

    async def new_user(self, event):
        """Broadcast: New user registration."""
        await self.send(text_data=json.dumps({
            'type': 'new_user',
            'data': event['data']
        }))

    async def new_analysis(self, event):
        """Broadcast: New analysis completed."""
        await self.send(text_data=json.dumps({
            'type': 'new_analysis',
            'data': event['data']
        }))

    async def alert_triggered(self, event):
        """Broadcast: Alert rule triggered."""
        await self.send(text_data=json.dumps({
            'type': 'alert_triggered',
            'data': event['data']
        }))


def send_admin_event(event_type: str, data: dict):
    """
    Sync helper to broadcast events from sync views to admin WS clients.

    Usage from sync views:
        from admin_api.consumers import send_admin_event
        send_admin_event('new_user', {'user_id': 123, 'email': 'user@example.com'})

    Args:
        event_type: str - event type (stat_update, new_user, new_analysis, alert_triggered)
        data: dict - event payload
    """
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            AdminLiveConsumer.GROUP_NAME,
            {
                'type': event_type,
                'data': data
            }
        )
    except Exception as e:
        log.warning(f'Failed to send admin event ({event_type}): {e}')
        # Don't raise — WS failure shouldn't break main operations
