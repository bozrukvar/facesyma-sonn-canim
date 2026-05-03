"""
analysis_api/community_chat_views.py
======================================
Topluluk grup chat REST API.

Endpoints:
  GET  /api/v1/communities/<id>/chat/messages/  → Sayfalı mesaj geçmişi
  POST /api/v1/communities/<id>/chat/messages/  → REST fallback (mesaj gönder)
  POST /api/v1/communities/<id>/chat/read/      → Okundu işaretle
"""

import json
import logging
import time
from datetime import datetime

import jwt
from bson import ObjectId
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.mongo import (
    get_users_col,
    get_community_messages_col,
    get_community_members_col,
)

log = logging.getLogger(__name__)

_JWT_SECRET: str = settings.JWT_SECRET
_MSG_PROJ = {
    '_id': 1, 'community_id': 1, 'sender_id': 1, 'sender_username': 1,
    'content': 1, 'type': 1, 'file_url': 1, 'file_name': 1, 'file_size_bytes': 1,
    'created_at': 1, 'read_by': 1,
}


def _get_user_id(request) -> int | None:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except Exception:
        return None


def _is_active_member(user_id: int, community_id: str) -> bool:
    member = get_community_members_col().find_one({
        'community_id': community_id,
        'user_id': user_id,
        'status': 'active',
    })
    return member is not None


def _serialize(doc: dict) -> dict:
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        else:
            out[k] = v
    return out


@method_decorator(csrf_exempt, name='dispatch')
class CommunityMessagesView(View):
    """GET/POST mesaj geçmişi + REST fallback."""

    def get(self, request, community_id: str):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        if not _is_active_member(user_id, community_id):
            return JsonResponse({'detail': 'Not a member of this community.'}, status=403)

        _qp = request.GET.get
        try:
            limit = min(max(1, int(_qp('limit', 50))), 100)
        except (ValueError, TypeError):
            limit = 50
        try:
            before = float(_qp('before', 0) or 0)
        except (ValueError, TypeError):
            before = 0

        query = {'community_id': community_id, 'deleted_at': None}
        if before:
            query['created_at'] = {'$lt': before}

        msgs = list(
            get_community_messages_col()
            .find(query, _MSG_PROJ)
            .sort('created_at', -1)
            .limit(limit + 1)
        )
        has_more = len(msgs) > limit
        msgs = msgs[:limit]
        msgs.reverse()

        return JsonResponse({
            'success': True,
            'data': [_serialize(m) for m in msgs],
            'count': len(msgs),
            'has_more': has_more,
        })

    def post(self, request, community_id: str):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        if not _is_active_member(user_id, community_id):
            return JsonResponse({'detail': 'Not a member of this community.'}, status=403)

        # 18+ yaş kontrolü
        user = get_users_col().find_one({'id': user_id}, {'birth_year': 1, 'username': 1, 'plan': 1})
        birth_year = (user or {}).get('birth_year')
        if birth_year and birth_year > datetime.utcnow().year - 18:
            return JsonResponse({'detail': 'age_restricted', 'min_age': 18}, status=403)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        content = str(data.get('content', '')).strip()[:2000]
        if not content:
            return JsonResponse({'detail': 'content is required.'}, status=400)

        username = (user or {}).get('username', f'user_{user_id}')
        now = time.time()
        msg_doc = {
            'community_id': community_id,
            'sender_id': user_id,
            'sender_username': username,
            'content': content,
            'type': 'text',
            'file_url': None,
            'file_name': None,
            'file_size_bytes': None,
            'created_at': now,
            'read_by': [user_id],
            'deleted_at': None,
        }
        result = get_community_messages_col().insert_one(msg_doc)
        msg_doc['_id'] = str(result.inserted_id)

        # Broadcast via WebSocket channel layer (best-effort)
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"community_room_{community_id}",
                    {'type': 'room_message', 'message': msg_doc}
                )
        except Exception:
            pass

        return JsonResponse({'success': True, 'message': msg_doc})


@method_decorator(csrf_exempt, name='dispatch')
class CommunityMarkReadView(View):
    """POST: okundu işaretle."""

    def post(self, request, community_id: str):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        if not _is_active_member(user_id, community_id):
            return JsonResponse({'detail': 'Not a member of this community.'}, status=403)

        get_community_messages_col().update_many(
            {'community_id': community_id, 'read_by': {'$ne': user_id}},
            {'$addToSet': {'read_by': user_id}}
        )
        return JsonResponse({'success': True})
