"""
analysis_api/peer_chat_views.py
================================
Uyumlu / aynı topluluk kullanıcıları arası P2P sohbet REST API'si.

Endpoints:
  POST   /api/v1/peer-chat/request/                    → Sohbet isteği gönder
  POST   /api/v1/peer-chat/request/<id>/respond/       → Kabul / Reddet
  GET    /api/v1/peer-chat/request/pending/             → Gelen bekleyen istekler
  GET    /api/v1/peer-chat/rooms/                       → Aktif oda listesi
  GET    /api/v1/peer-chat/rooms/<room_id>/messages/    → Mesaj geçmişi (sayfalı)
  POST   /api/v1/peer-chat/rooms/<room_id>/messages/    → Mesaj gönder (REST fallback)
  POST   /api/v1/peer-chat/rooms/<room_id>/read/        → Okundu işaretle
  DELETE /api/v1/peer-chat/rooms/<room_id>/             → Odadan ayrıl
  POST   /api/v1/peer-chat/upload/                      → Dosya yükle (premium, 10 MB)
"""

import json
import logging
import time
import os
import uuid
from datetime import date

import jwt
from bson import ObjectId
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.mongo import (
    get_users_col,
    get_peer_chat_requests_col,
    get_peer_chat_rooms_col,
    get_peer_messages_col,
)

log = logging.getLogger(__name__)

_JWT_SECRET: str = settings.JWT_SECRET

# ── Limitler ──────────────────────────────────────────────────────────────────
_PEER_DAILY_LIMITS = {'free': 5, 'premium': 200}
_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_REQUEST_EXPIRE_SECONDS = 48 * 3600  # 48 saat
_MIN_MODULES_FOR_FREE = 3

# ── Projection sabitleri ───────────────────────────────────────────────────────
_USER_PROJ  = {'_id': 0, 'id': 1, 'username': 1, 'plan': 1, 'modules': 1}
_MSG_PROJ   = {'_id': 1, 'room_id': 1, 'sender_id': 1, 'content': 1,
               'type': 1, 'file_url': 1, 'file_name': 1, 'file_size_bytes': 1,
               'created_at': 1, 'read_by': 1}
_ROOM_PROJ  = {'_id': 1, 'room_id': 1, 'user_ids': 1, 'source': 1,
               'compatibility_score': 1, 'created_at': 1,
               'last_message_at': 1, 'last_message_preview': 1,
               'unread_counts': 1, 'is_active': 1}
_REQ_PROJ   = {'_id': 1, 'from_user_id': 1, 'to_user_id': 1,
               'compatibility_score': 1, 'source': 1,
               'status': 1, 'created_at': 1, 'expires_at': 1}


# ── Yardımcı fonksiyonlar ──────────────────────────────────────────────────────

def _get_user_id(request) -> int | None:
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except Exception:
        return None


def _get_user(user_id: int) -> dict | None:
    return get_users_col().find_one({'id': user_id}, _USER_PROJ)


def _get_plan(user: dict) -> str:
    return user.get('plan', 'free') if user else 'free'


def _check_chat_unlock(user: dict) -> tuple[bool, str]:
    """(allowed, reason) — premium direkt geçer, free 3 modül ister."""
    if _get_plan(user) == 'premium':
        return True, ''
    modules = user.get('modules', [])
    if len(set(modules)) < _MIN_MODULES_FOR_FREE:
        needed = _MIN_MODULES_FOR_FREE - len(set(modules))
        return False, f'Chat için en az {_MIN_MODULES_FOR_FREE} modül kullanman gerekiyor. {needed} modül daha kullan.'
    return True, ''


def _daily_msg_key(user_id: int) -> str:
    return f"peer_chat:daily:{user_id}:{date.today().isoformat()}"


def _check_daily_limit(user_id: int, plan: str) -> tuple[bool, int, int]:
    """(allowed, used, limit). Redis yoksa her zaman izin ver."""
    limit = _PEER_DAILY_LIMITS.get(plan, _PEER_DAILY_LIMITS['free'])
    if plan == 'premium':
        return True, 0, limit
    try:
        from core.redis_client import get_redis
        r = get_redis()
        if r is None:
            return True, 0, limit
        key = _daily_msg_key(user_id)
        used = int(r.get(key) or 0)
        if used >= limit:
            return False, used, limit
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)
        pipe.execute()
        return True, used + 1, limit
    except Exception:
        return True, 0, limit


def _can_start_chat(from_id: int, to_id: int) -> tuple[bool, str]:
    """İki kullanıcı uyumlu mu veya ortak aktif toplulukları var mı?"""
    from admin_api.utils.mongo import _get_db
    db = _get_db()

    # Yol 1: Uyumluluk analizi
    compat = db['compatibility'].find_one(
        {'$or': [
            {'user1_id': from_id, 'user2_id': to_id},
            {'user1_id': to_id,   'user2_id': from_id},
        ]},
        {'can_message': 1, 'score': 1}
    )
    if compat and compat.get('can_message'):
        return True, 'compatibility'

    # Yol 2: Ortak aktif topluluk üyeliği
    members_col = db['community_members']
    from_comms = {m['community_id'] for m in members_col.find(
        {'user_id': from_id, 'status': 'active'}, {'community_id': 1}
    )}
    if from_comms:
        to_comms = {m['community_id'] for m in members_col.find(
            {'user_id': to_id, 'status': 'active'}, {'community_id': 1}
        )}
        if from_comms & to_comms:
            return True, 'community'

    return False, ''


def _room_id(uid1: int, uid2: int) -> str:
    a, b = sorted([uid1, uid2])
    return f"room_{a}_{b}"


def _serialize_doc(doc: dict) -> dict:
    """ObjectId → str dönüştür."""
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        else:
            out[k] = v
    return out


# ── Views ─────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class SendChatRequestView(View):
    """POST /api/v1/peer-chat/request/ — Sohbet isteği gönder."""

    def post(self, request):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        user = _get_user(user_id)
        if not user:
            return JsonResponse({'detail': 'User not found.'}, status=404)

        # Kilit kontrolü
        unlocked, reason = _check_chat_unlock(user)
        if not unlocked:
            return JsonResponse({'detail': reason, 'code': 'chat_locked'}, status=403)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        to_user_id = data.get('to_user_id')
        if not to_user_id or to_user_id == user_id:
            return JsonResponse({'detail': 'Geçerli bir to_user_id gerekli.'}, status=400)

        # Hedef kullanıcı var mı?
        to_user = _get_user(to_user_id)
        if not to_user:
            return JsonResponse({'detail': 'Hedef kullanıcı bulunamadı.'}, status=404)

        # Chat başlatma yetkisi var mı?
        allowed, source = _can_start_chat(user_id, to_user_id)
        if not allowed:
            return JsonResponse({
                'detail': 'Sohbet başlatmak için uyumlu olmanız veya ortak bir toplulukta bulunmanız gerekiyor.',
                'code': 'not_compatible'
            }, status=403)

        requests_col = get_peer_chat_requests_col()
        now = time.time()

        # Zaten aktif oda var mı?
        room_id_str = _room_id(user_id, to_user_id)
        existing_room = get_peer_chat_rooms_col().find_one(
            {'room_id': room_id_str, 'is_active': True}
        )
        if existing_room:
            return JsonResponse({
                'detail': 'Bu kullanıcıyla zaten aktif bir sohbetiniz var.',
                'room_id': room_id_str
            }, status=200)

        # Bekleyen istek var mı?
        existing_req = requests_col.find_one({
            'from_user_id': user_id,
            'to_user_id': to_user_id,
            'status': 'pending',
        })
        if existing_req:
            return JsonResponse({
                'detail': 'Bu kullanıcıya zaten bekleyen bir isteğiniz var.',
                'request_id': str(existing_req['_id'])
            }, status=200)

        req_doc = {
            'from_user_id': user_id,
            'from_username': user.get('username', ''),
            'to_user_id': to_user_id,
            'compatibility_score': data.get('compatibility_score', 0.0),
            'source': source,
            'status': 'pending',
            'created_at': now,
            'expires_at': now + _REQUEST_EXPIRE_SECONDS,
            'responded_at': None,
        }
        result = requests_col.insert_one(req_doc)

        # WS üzerinden hedef kullanıcıya bildirim gönder
        try:
            from analysis_api.peer_chat_consumers import send_peer_event
            send_peer_event(to_user_id, 'chat_request', {
                'request_id': str(result.inserted_id),
                'from_user_id': user_id,
                'from_username': user.get('username', ''),
                'source': source,
            })
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'request_id': str(result.inserted_id),
            'message': 'Sohbet isteği gönderildi. Karşı tarafın onayı bekleniyor.'
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class RespondChatRequestView(View):
    """POST /api/v1/peer-chat/request/<id>/respond/ — Kabul veya reddet."""

    def post(self, request, request_id=None):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        action = data.get('action', '').lower()
        if action not in ('accept', 'reject'):
            return JsonResponse({'detail': 'action must be "accept" or "reject".'}, status=400)

        try:
            oid = ObjectId(request_id)
        except Exception:
            return JsonResponse({'detail': 'Geçersiz request_id.'}, status=400)

        requests_col = get_peer_chat_requests_col()
        req = requests_col.find_one({'_id': oid, 'to_user_id': user_id})
        if not req:
            return JsonResponse({'detail': 'İstek bulunamadı.'}, status=404)

        if req['status'] != 'pending':
            return JsonResponse({'detail': f'İstek zaten {req["status"]} durumunda.'}, status=409)

        now = time.time()
        if req.get('expires_at', 0) < now:
            requests_col.update_one({'_id': oid}, {'$set': {'status': 'expired'}})
            return JsonResponse({'detail': 'İstek süresi dolmuş.'}, status=410)

        requests_col.update_one(
            {'_id': oid},
            {'$set': {'status': action + 'ed', 'responded_at': now}}
        )

        room_id_str = None
        if action == 'accept':
            # Oda oluştur
            from_id = req['from_user_id']
            room_id_str = _room_id(from_id, user_id)
            rooms_col = get_peer_chat_rooms_col()
            existing = rooms_col.find_one({'room_id': room_id_str})
            if not existing:
                rooms_col.insert_one({
                    'room_id': room_id_str,
                    'user_ids': sorted([from_id, user_id]),
                    'request_id': oid,
                    'source': req.get('source', 'unknown'),
                    'compatibility_score': req.get('compatibility_score', 0.0),
                    'created_at': now,
                    'last_message_at': None,
                    'last_message_preview': '',
                    'unread_counts': {str(from_id): 0, str(user_id): 0},
                    'is_active': True,
                })

            # Her iki kullanıcıya WS bildirimi
            try:
                from analysis_api.peer_chat_consumers import send_peer_event
                for uid in [from_id, user_id]:
                    send_peer_event(uid, 'request_update', {
                        'request_id': str(oid),
                        'status': 'accepted',
                        'room_id': room_id_str,
                    })
            except Exception:
                pass

        else:
            try:
                from analysis_api.peer_chat_consumers import send_peer_event
                send_peer_event(req['from_user_id'], 'request_update', {
                    'request_id': str(oid),
                    'status': 'rejected',
                })
            except Exception:
                pass

        resp = {'success': True, 'status': action + 'ed'}
        if room_id_str:
            resp['room_id'] = room_id_str
        return JsonResponse(resp)


@method_decorator(csrf_exempt, name='dispatch')
class PendingRequestsView(View):
    """GET /api/v1/peer-chat/request/pending/ — Gelen bekleyen istekler."""

    def get(self, request):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        now = time.time()
        requests_col = get_peer_chat_requests_col()
        pending = list(requests_col.find(
            {'to_user_id': user_id, 'status': 'pending', 'expires_at': {'$gt': now}},
            _REQ_PROJ
        ).sort('created_at', -1).limit(50))

        # Gönderen kullanıcı bilgilerini zenginleştir
        from_ids = [r['from_user_id'] for r in pending]
        users_map = {u['id']: u for u in get_users_col().find(
            {'id': {'$in': from_ids}}, {'id': 1, 'username': 1}
        )}
        for r in pending:
            u = users_map.get(r['from_user_id'], {})
            r['from_username'] = u.get('username', 'Unknown')

        return JsonResponse({
            'success': True,
            'data': [_serialize_doc(r) for r in pending],
            'count': len(pending)
        })


@method_decorator(csrf_exempt, name='dispatch')
class ChatRoomsView(View):
    """GET /api/v1/peer-chat/rooms/ — Aktif sohbet odaları."""

    def get(self, request):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        rooms_col = get_peer_chat_rooms_col()
        rooms = list(rooms_col.find(
            {'user_ids': user_id, 'is_active': True},
            _ROOM_PROJ
        ).sort('last_message_at', -1).limit(100))

        # Diğer kullanıcı bilgisini ekle
        other_ids = []
        for r in rooms:
            for uid in r.get('user_ids', []):
                if uid != user_id:
                    other_ids.append(uid)

        users_map = {u['id']: u for u in get_users_col().find(
            {'id': {'$in': other_ids}}, {'id': 1, 'username': 1}
        )}
        for r in rooms:
            for uid in r.get('user_ids', []):
                if uid != user_id:
                    u = users_map.get(uid, {})
                    r['other_user'] = {'id': uid, 'username': u.get('username', 'Unknown')}
                    r['my_unread'] = r.get('unread_counts', {}).get(str(user_id), 0)
                    break

        return JsonResponse({
            'success': True,
            'data': [_serialize_doc(r) for r in rooms],
            'count': len(rooms)
        })


@method_decorator(csrf_exempt, name='dispatch')
class ChatMessagesView(View):
    """
    GET  /api/v1/peer-chat/rooms/<room_id>/messages/ — Mesaj geçmişi
    POST /api/v1/peer-chat/rooms/<room_id>/messages/ — Mesaj gönder (REST fallback)
    """

    def _get_room(self, room_id: str, user_id: int):
        return get_peer_chat_rooms_col().find_one(
            {'room_id': room_id, 'user_ids': user_id, 'is_active': True}
        )

    def get(self, request, room_id=None):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        room = self._get_room(room_id, user_id)
        if not room:
            return JsonResponse({'detail': 'Oda bulunamadı.'}, status=404)

        try:
            before = float(request.GET.get('before', time.time()))
            limit = min(max(1, int(request.GET.get('limit', 50))), 100)
        except (ValueError, TypeError):
            before, limit = time.time(), 50

        msgs = list(get_peer_messages_col().find(
            {'room_id': room_id, 'created_at': {'$lt': before}, 'deleted_at': None},
            _MSG_PROJ
        ).sort('created_at', -1).limit(limit))

        msgs.reverse()
        return JsonResponse({
            'success': True,
            'data': [_serialize_doc(m) for m in msgs],
            'count': len(msgs),
            'has_more': len(msgs) == limit
        })

    def post(self, request, room_id=None):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        room = self._get_room(room_id, user_id)
        if not room:
            return JsonResponse({'detail': 'Oda bulunamadı.'}, status=404)

        user = _get_user(user_id)
        plan = _get_plan(user)

        allowed, used, limit = _check_daily_limit(user_id, plan)
        if not allowed:
            return JsonResponse({
                'detail': f'Günlük mesaj limitine ({limit}) ulaştınız.',
                'used': used, 'limit': limit,
                'code': 'daily_limit_reached'
            }, status=429)

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        content = (data.get('content') or '').strip()
        if not content:
            return JsonResponse({'detail': 'Mesaj boş olamaz.'}, status=400)

        now = time.time()
        msg_doc = {
            'room_id': room_id,
            'sender_id': user_id,
            'content': content[:2000],
            'type': 'text',
            'file_url': None,
            'file_name': None,
            'file_size_bytes': None,
            'created_at': now,
            'read_by': [user_id],
            'deleted_at': None,
        }
        result = get_peer_messages_col().insert_one(msg_doc)
        msg_doc['_id'] = result.inserted_id

        # Oda güncelle
        other_ids = [uid for uid in room.get('user_ids', []) if uid != user_id]
        unread_inc = {f'unread_counts.{str(uid)}': 1 for uid in other_ids}
        get_peer_chat_rooms_col().update_one(
            {'room_id': room_id},
            {'$set': {
                'last_message_at': now,
                'last_message_preview': content[:80],
            }, '$inc': unread_inc}
        )

        # WS broadcast
        try:
            from analysis_api.peer_chat_consumers import broadcast_room_message
            broadcast_room_message(room_id, _serialize_doc(msg_doc))
        except Exception:
            pass

        return JsonResponse({'success': True, 'message': _serialize_doc(msg_doc)}, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class MarkReadView(View):
    """POST /api/v1/peer-chat/rooms/<room_id>/read/ — Okundu işaretle."""

    def post(self, request, room_id=None):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        room = get_peer_chat_rooms_col().find_one(
            {'room_id': room_id, 'user_ids': user_id, 'is_active': True}
        )
        if not room:
            return JsonResponse({'detail': 'Oda bulunamadı.'}, status=404)

        now = time.time()
        get_peer_messages_col().update_many(
            {'room_id': room_id, 'read_by': {'$ne': user_id}, 'deleted_at': None},
            {'$push': {'read_by': user_id}}
        )
        get_peer_chat_rooms_col().update_one(
            {'room_id': room_id},
            {'$set': {f'unread_counts.{str(user_id)}': 0}}
        )

        try:
            from analysis_api.peer_chat_consumers import send_room_event
            send_room_event(room_id, 'read_receipt', {'user_id': user_id, 'time': now})
        except Exception:
            pass

        return JsonResponse({'success': True})


@method_decorator(csrf_exempt, name='dispatch')
class LeaveChatRoomView(View):
    """DELETE /api/v1/peer-chat/rooms/<room_id>/ — Odadan ayrıl."""

    def delete(self, request, room_id=None):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        result = get_peer_chat_rooms_col().update_one(
            {'room_id': room_id, 'user_ids': user_id, 'is_active': True},
            {'$set': {'is_active': False}}
        )
        if result.matched_count == 0:
            return JsonResponse({'detail': 'Oda bulunamadı.'}, status=404)

        return JsonResponse({'success': True})


@method_decorator(csrf_exempt, name='dispatch')
class UploadChatFileView(View):
    """POST /api/v1/peer-chat/upload/ — Dosya yükle (sadece premium, max 10 MB)."""

    def post(self, request):
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)

        user = _get_user(user_id)
        if _get_plan(user) != 'premium':
            return JsonResponse({
                'detail': 'Dosya paylaşımı sadece premium kullanıcılara açıktır.',
                'code': 'premium_required'
            }, status=403)

        uploaded = request.FILES.get('file')
        if not uploaded:
            return JsonResponse({'detail': 'Dosya bulunamadı.'}, status=400)

        if uploaded.size > _FILE_MAX_BYTES:
            return JsonResponse({
                'detail': f'Dosya 10 MB sınırını aşıyor ({uploaded.size // (1024*1024)} MB).',
                'code': 'file_too_large'
            }, status=413)

        room_id = request.POST.get('room_id', '')
        if room_id:
            room = get_peer_chat_rooms_col().find_one(
                {'room_id': room_id, 'user_ids': user_id, 'is_active': True}
            )
            if not room:
                return JsonResponse({'detail': 'Oda bulunamadı.'}, status=404)

        # Dosyayı media dizinine kaydet
        ext = os.path.splitext(uploaded.name)[1].lower()
        filename = f"chat_{user_id}_{uuid.uuid4().hex}{ext}"
        media_root = getattr(settings, 'MEDIA_ROOT', '/tmp/chat_files')
        os.makedirs(media_root, exist_ok=True)
        filepath = os.path.join(media_root, filename)

        with open(filepath, 'wb') as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        file_url = f"{media_url}{filename}"

        # Oda varsa mesaj olarak kaydet
        if room_id:
            now = time.time()
            ftype = 'image' if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp') else 'file'
            msg_doc = {
                'room_id': room_id,
                'sender_id': user_id,
                'content': uploaded.name,
                'type': ftype,
                'file_url': file_url,
                'file_name': uploaded.name,
                'file_size_bytes': uploaded.size,
                'created_at': now,
                'read_by': [user_id],
                'deleted_at': None,
            }
            result = get_peer_messages_col().insert_one(msg_doc)
            msg_doc['_id'] = result.inserted_id

            other_ids = [uid for uid in room.get('user_ids', []) if uid != user_id]
            unread_inc = {f'unread_counts.{str(uid)}': 1 for uid in other_ids}
            get_peer_chat_rooms_col().update_one(
                {'room_id': room_id},
                {'$set': {'last_message_at': now, 'last_message_preview': f'📎 {uploaded.name}'},
                 '$inc': unread_inc}
            )

            try:
                from analysis_api.peer_chat_consumers import broadcast_room_message
                broadcast_room_message(room_id, _serialize_doc(msg_doc))
            except Exception:
                pass

            return JsonResponse({
                'success': True,
                'file_url': file_url,
                'message': _serialize_doc(msg_doc)
            }, status=201)

        return JsonResponse({'success': True, 'file_url': file_url}, status=201)
