"""
analysis_api/peer_chat_consumers.py
=====================================
P2P sohbet WebSocket consumer.

URL: ws/chat/<room_id>/?token=<jwt>

Client → Server mesaj tipleri:
  send_message  : {type, content}
  typing        : {type}
  ping          : {type}

Server → Client mesaj tipleri:
  new_message   : {type, message}
  typing        : {type, user_id}
  read_receipt  : {type, user_id, time}
  request_update: {type, request_id, status, room_id?}
  chat_request  : {type, request_id, from_user_id, from_username, source}
  pong          : {type}
  error         : {type, detail}
"""

import json
import logging
import time

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

log = logging.getLogger(__name__)

_JWT_SECRET: str = settings.JWT_SECRET

# ── Yardımcı: kullanıcıya özel bildirim kanalı adı ────────────────────────────

def _user_group(user_id: int) -> str:
    return f"peer_user_{user_id}"


def _room_group(room_id: str) -> str:
    return f"peer_room_{room_id}"


# ── Sync yardımcılar (view'lardan çağrılır) ────────────────────────────────────

def send_peer_event(to_user_id: int, event_type: str, data: dict) -> None:
    """Belirli bir kullanıcıya WS olayı gönder (sync, view'lardan çağrılır)."""
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            _user_group(to_user_id),
            {'type': 'peer_event', 'event_type': event_type, 'data': data}
        )
    except Exception as e:
        log.debug(f"send_peer_event failed: {e}")


def broadcast_room_message(room_id: str, message: dict) -> None:
    """Oda grubuna yeni mesaj yayınla (sync, view'lardan çağrılır)."""
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            _room_group(room_id),
            {'type': 'room_message', 'message': message}
        )
    except Exception as e:
        log.debug(f"broadcast_room_message failed: {e}")


def send_room_event(room_id: str, event_type: str, data: dict) -> None:
    """Oda grubuna genel olay yayınla (typing, read_receipt vb.)."""
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            _room_group(room_id),
            {'type': 'room_event', 'event_type': event_type, 'data': data}
        )
    except Exception as e:
        log.debug(f"send_room_event failed: {e}")


# ── Consumer ──────────────────────────────────────────────────────────────────

class PeerChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = None
        self.room_id = self.scope['url_route']['kwargs'].get('room_id', '')
        self.room_group = _room_group(self.room_id)
        self.user_group = None

        # JWT doğrula
        token = self._extract_token()
        if not token:
            await self.close(code=4001)
            return

        user_id = self._decode_token(token)
        if not user_id:
            await self.close(code=4001)
            return

        # Oda erişim yetkisi kontrol et
        if not await self._verify_room_access(user_id, self.room_id):
            await self.close(code=4003)
            return

        self.user_id = user_id
        self.user_group = _user_group(user_id)

        # Oda grubuna ve kullanıcı grubuna katıl
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        log.info(f"PeerChat: user {user_id} joined room {self.room_id}")

    async def disconnect(self, close_code):
        if self.room_group:
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        if self.user_group:
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error('Invalid JSON.')
            return

        msg_type = data.get('type', '')

        if msg_type == 'send_message':
            await self._handle_send_message(data)
        elif msg_type == 'typing':
            await self._handle_typing()
        elif msg_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
        else:
            await self._send_error(f'Unknown message type: {msg_type}')

    # ── Mesaj gönderme ──────────────────────────────────────────────────────────

    async def _handle_send_message(self, data: dict):
        content = (data.get('content') or '').strip()
        if not content:
            await self._send_error('Mesaj boş olamaz.')
            return

        # Günlük limit kontrolü (sync DB çağrısı)
        from asgiref.sync import sync_to_async
        allowed, used, limit = await sync_to_async(self._check_limit)()
        if not allowed:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'daily_limit_reached',
                'detail': f'Günlük mesaj limitine ({limit}) ulaştınız.',
                'used': used,
                'limit': limit,
            }))
            return

        now = time.time()
        msg_doc = {
            'room_id': self.room_id,
            'sender_id': self.user_id,
            'content': content[:2000],
            'type': 'text',
            'file_url': None,
            'file_name': None,
            'file_size_bytes': None,
            'created_at': now,
            'read_by': [self.user_id],
            'deleted_at': None,
        }

        # Async DB kayıt
        msg_id = await sync_to_async(self._save_message)(msg_doc)
        msg_doc['_id'] = msg_id

        payload = {k: (str(v) if hasattr(v, '__class__') and v.__class__.__name__ == 'ObjectId' else v)
                   for k, v in msg_doc.items()}

        # Odadaki herkese broadcast
        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'room_message', 'message': payload}
        )

    async def _handle_typing(self):
        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'room_event', 'event_type': 'typing', 'data': {'user_id': self.user_id}}
        )

    # ── Channel layer event handler'ları ──────────────────────────────────────

    async def room_message(self, event):
        """Oda grubundan gelen yeni mesajı istemciye ilet."""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def room_event(self, event):
        """Typing, read_receipt gibi oda olaylarını ilet."""
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            **event['data']
        }))

    async def peer_event(self, event):
        """Kullanıcıya özel olayları ilet (chat_request, request_update)."""
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            **event['data']
        }))

    # ── Yardımcılar ────────────────────────────────────────────────────────────

    def _extract_token(self) -> str | None:
        qs = self.scope.get('query_string', b'').decode()
        for part in qs.split('&'):
            if part.startswith('token='):
                return part[6:]
        return None

    def _decode_token(self, token: str) -> int | None:
        try:
            payload = jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])
            return payload.get('user_id')
        except Exception:
            return None

    async def _verify_room_access(self, user_id: int, room_id: str) -> bool:
        if not room_id:
            return False
        from asgiref.sync import sync_to_async
        return await sync_to_async(self._check_room_access)(user_id, room_id)

    def _check_room_access(self, user_id: int, room_id: str) -> bool:
        from admin_api.utils.mongo import get_peer_chat_rooms_col
        room = get_peer_chat_rooms_col().find_one(
            {'room_id': room_id, 'user_ids': user_id, 'is_active': True}
        )
        return room is not None

    def _check_limit(self) -> tuple:
        from analysis_api.peer_chat_views import _get_user, _get_plan, _check_daily_limit
        user = _get_user(self.user_id)
        plan = _get_plan(user)
        return _check_daily_limit(self.user_id, plan)

    def _save_message(self, msg_doc: dict):
        from admin_api.utils.mongo import get_peer_chat_rooms_col, get_peer_messages_col
        result = get_peer_messages_col().insert_one(dict(msg_doc))
        # Oda güncelle
        room = get_peer_chat_rooms_col().find_one({'room_id': msg_doc['room_id']})
        if room:
            other_ids = [uid for uid in room.get('user_ids', []) if uid != self.user_id]
            unread_inc = {f'unread_counts.{str(uid)}': 1 for uid in other_ids}
            get_peer_chat_rooms_col().update_one(
                {'room_id': msg_doc['room_id']},
                {'$set': {
                    'last_message_at': msg_doc['created_at'],
                    'last_message_preview': msg_doc['content'][:80],
                }, '$inc': unread_inc}
            )
        return result.inserted_id

    async def _send_error(self, detail: str):
        await self.send(text_data=json.dumps({'type': 'error', 'detail': detail}))
