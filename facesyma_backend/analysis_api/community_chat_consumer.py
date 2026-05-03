"""
analysis_api/community_chat_consumer.py
=========================================
Topluluk grup chat WebSocket consumer.

URL: ws/community/<community_id>/chat/?token=<jwt>

Client → Server mesaj tipleri:
  send_message : {type, content}
  typing       : {type}
  ping         : {type}

Server → Client mesaj tipleri:
  new_message  : {type, message}
  typing       : {type, user_id, username}
  pong         : {type}
  error        : {type, code, detail}
"""

import json
import logging
import time
from datetime import datetime

import jwt
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

log = logging.getLogger(__name__)

_JWT_SECRET: str = settings.JWT_SECRET


def _community_group(community_id: str) -> str:
    return f"community_room_{community_id}"


class CommunityChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = None
        self.username = ''
        self.community_id = self.scope['url_route']['kwargs'].get('community_id', '')
        self.room_group = _community_group(self.community_id)

        token = self._extract_token()
        if not token:
            await self.close(code=4001)
            return

        user_id, username = await sync_to_async(self._decode_token)(token)
        if not user_id:
            await self.close(code=4001)
            return

        # Aktif üyelik kontrolü
        if not await sync_to_async(self._check_membership)(user_id, self.community_id):
            await self.close(code=4003)
            return

        self.user_id = user_id
        self.username = username or f'user_{user_id}'

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        log.info(f"CommunityChat: user {user_id} joined community {self.community_id}")

    async def disconnect(self, close_code):
        if self.room_group:
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error('invalid_json', 'Invalid JSON.')
            return

        msg_type = data.get('type', '')
        if msg_type == 'send_message':
            await self._handle_send_message(data)
        elif msg_type == 'typing':
            await self._handle_typing()
        elif msg_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
        else:
            await self._send_error('unknown_type', f'Unknown message type: {msg_type}')

    async def _handle_send_message(self, data: dict):
        content = (data.get('content') or '').strip()
        if not content:
            await self._send_error('empty_message', 'Mesaj boş olamaz.')
            return

        # 18+ yaş kontrolü
        is_adult = await sync_to_async(self._check_adult)()
        if not is_adult:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'age_restricted',
                'min_age': 18,
            }))
            return

        # Günlük limit kontrolü
        allowed, used, limit = await sync_to_async(self._check_limit)()
        if not allowed:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'daily_limit_reached',
                'detail': f'Günlük mesaj limitine ({limit}) ulaştınız.',
                'used': used, 'limit': limit,
            }))
            return

        now = time.time()
        msg_doc = {
            'community_id': self.community_id,
            'sender_id': self.user_id,
            'sender_username': self.username,
            'content': content[:2000],
            'type': 'text',
            'file_url': None,
            'file_name': None,
            'file_size_bytes': None,
            'created_at': now,
            'read_by': [self.user_id],
            'deleted_at': None,
        }

        msg_id = await sync_to_async(self._save_message)(msg_doc)
        msg_doc['_id'] = str(msg_id)

        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'room_message', 'message': msg_doc}
        )

    async def _handle_typing(self):
        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'room_event', 'event_type': 'typing',
             'data': {'user_id': self.user_id, 'username': self.username}}
        )

    async def room_message(self, event):
        await self.send(text_data=json.dumps({'type': 'new_message', 'message': event['message']}))

    async def room_event(self, event):
        await self.send(text_data=json.dumps({'type': event['event_type'], **event['data']}))

    # ── Yardımcılar ────────────────────────────────────────────────────────────

    def _extract_token(self) -> str | None:
        qs = self.scope.get('query_string', b'').decode()
        for part in qs.split('&'):
            if part.startswith('token='):
                return part[6:]
        return None

    def _decode_token(self, token: str) -> tuple[int | None, str]:
        try:
            payload = jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                return None, ''
            from admin_api.utils.mongo import get_users_col
            user = get_users_col().find_one({'id': user_id}, {'username': 1})
            username = user.get('username', '') if user else ''
            return user_id, username
        except Exception:
            return None, ''

    def _check_membership(self, user_id: int, community_id: str) -> bool:
        from admin_api.utils.mongo import get_community_members_col
        member = get_community_members_col().find_one({
            'community_id': community_id,
            'user_id': user_id,
            'status': 'active',
        })
        return member is not None

    def _check_adult(self) -> bool:
        from admin_api.utils.mongo import get_users_col
        user = get_users_col().find_one({'id': self.user_id}, {'birth_year': 1})
        if not user:
            return True
        birth_year = user.get('birth_year')
        if not birth_year:
            return True
        return birth_year <= datetime.utcnow().year - 18

    def _check_limit(self) -> tuple:
        from analysis_api.peer_chat_views import _get_user, _get_plan, _check_daily_limit
        user = _get_user(self.user_id)
        plan = _get_plan(user)
        return _check_daily_limit(self.user_id, plan)

    def _save_message(self, msg_doc: dict):
        from admin_api.utils.mongo import get_community_messages_col
        result = get_community_messages_col().insert_one(dict(msg_doc))
        return result.inserted_id

    async def _send_error(self, code: str, detail: str):
        await self.send(text_data=json.dumps({'type': 'error', 'code': code, 'detail': detail}))
