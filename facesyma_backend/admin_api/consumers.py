"""
admin_api/consumers.py
======================
WebSocket consumer for real-time admin dashboard updates.

Broadcast helpers allow sync views to push events to connected admin clients.
"""

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
import json
import logging
import jwt
from urllib.parse import parse_qs
from django.conf import settings
from admin_api.utils.mongo import get_admin_col

log = logging.getLogger(__name__)

_ADMIN_JWT_SECRET: str = settings.ADMIN_JWT_SECRET


def _verify_admin_token(token: str) -> bool:
    """Verify an admin JWT synchronously — runs in thread pool via sync_to_async."""
    try:
        payload = jwt.decode(token, _ADMIN_JWT_SECRET, algorithms=['HS256'])
        _pget = payload.get
        if _pget('type') != 'admin_access' or not _pget('is_admin'):
            return False
        col = get_admin_col()
        admin = col.find_one({'id': _pget('admin_id')}, {'_id': 0, 'is_active': 1})
        return bool(admin and admin.get('is_active'))
    except Exception:
        return False


class AdminLiveConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live admin dashboard."""

    GROUP_NAME = 'admin_live'

    async def connect(self):
        """Authenticate via ?token= query param, then join broadcast group."""
        qs = parse_qs(self.scope.get('query_string', b'').decode())
        token = (qs.get('token') or [''])[0]
        if not token or not await sync_to_async(_verify_admin_token)(token):
            log.warning(f'Admin WS rejected unauthenticated connection')
            await self.close(code=4401)
            return
        _cn = self.channel_name
        await self.channel_layer.group_add(self.GROUP_NAME, _cn)
        await self.accept()
        log.debug(f'Admin WS client connected: {_cn}')

    async def disconnect(self, close_code):
        """Remove consumer from broadcast group."""
        _cn = self.channel_name
        await self.channel_layer.group_discard(self.GROUP_NAME, _cn)
        log.debug(f'Admin WS client disconnected: {_cn}')

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
