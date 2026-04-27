"""
compatibility_views.py
======================
Phase 1 API Endpoints for Compatibility Matching & Communities.

Endpoints:
  POST   /api/v1/compatibility/check/     → CheckCompatibilityView
  POST   /api/v1/compatibility/find/      → FindCompatibleUsersView
  GET    /api/v1/compatibility/stats/     → CompatibilityStatsView
  GET    /api/v1/communities/             → ListCommunitiesView
  POST   /api/v1/communities/<id>/join/   → JoinCommunityView
  GET    /api/v1/communities/<id>/members/→ ListCommunityMembersView
"""
import json
import logging
import time
import jwt
from functools import wraps
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from bson import ObjectId
from django.conf import settings
import sys

log = logging.getLogger(__name__)

_VALID_CATEGORIES = frozenset({'TRAIT', 'MODULE', 'CATEGORY', 'GENERAL'})
_VALID_COMMUNITY_TYPES = frozenset({'TRAIT', 'MODULE', 'CATEGORY', 'GENERAL'})
_PROJ_PENDING_INVITE = {'_id': 0, 'community_id': 1, 'invited_at': 1, 'harmony_level': 1}
_PROJ_COMMUNITY_BRIEF = {'name': 1, 'type': 1, 'trait_name': 1}

_USER_COMPAT_PROJ    = {'_id': 0, 'id': 1, 'username': 1, 'golden_ratio': 1, 'top_sifats': 1, 'modules': 1}
_COMMUNITY_LIST_PROJ = {'_id': 1, 'name': 1, 'type': 1, 'trait_name': 1, 'member_count': 1,
                        'description': 1, 'created_at': 1, 'is_active': 1}
_MEMBER_PROJ         = {'_id': 0, 'user_id': 1, 'harmony_level': 1, 'joined_at': 1, 'is_mod': 1}
_SUB_STATUS_PROJ     = {'_id': 0, 'user_id': 1, 'tier': 1, 'status': 1, 'renews_at': 1}
_JWT_SECRET: str = settings.JWT_SECRET

# ── JWT yardımcısı ────────────────────────────────────────────────────────────
def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar. Token yoksa None döner."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(
            auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256']
        )
        return payload.get('user_id')
    except Exception:
        return None


# ── Veritabanı koleksiyonları ─────────────────────────────────────────────────
def _get_db():
    """Get facesyma-backend database with pooled connection"""
    from admin_api.utils.mongo import _get_main_client
    return _get_main_client()['facesyma-backend']


def _get_compatibility_col():
    return _get_db()['compatibility']


def _get_communities_col():
    return _get_db()['communities']


def _get_community_members_col():
    return _get_db()['community_members']


_ENGINE_PATH: str = settings.FACESYMA_ENGINE_PATH

# ── Compatibility Algorithm ───────────────────────────────────────────────────
def _load_compatibility_module():
    """compatibility.py modülünü yükle"""
    _spath = sys.path
    if _ENGINE_PATH not in _spath:
        _spath.insert(0, _ENGINE_PATH)

    try:
        # Lazy import to avoid circular dependencies
        from compatibility import calculate_compatibility, find_compatible_users
        return calculate_compatibility, find_compatible_users
    except ImportError as e:
        log.warning(f'Compatibility module import failed: {e}')
        return None, None


# ── Helper: Kullanıcı profilini al ──────────────────────────────────────────
def _get_user_profile(user_id):
    """
    Kullanıcının profil bilgisini al.

    Returns: {user_id, username, golden_ratio, top_sifats, modules}
    """
    from admin_api.utils.mongo import get_users_col

    users_col = get_users_col()
    user = users_col.find_one({'id': user_id}, _USER_COMPAT_PROJ)

    if not user:
        return None

    # Eksik alanlar için defaults
    _usd = user.setdefault
    _usd('golden_ratio', 1.618)
    _usd('top_sifats', [])
    _usd('modules', [])

    return user


# ── Views ──────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CheckCompatibilityView(View):
    """
    POST /api/v1/compatibility/check/

    İki kullanıcı arası uyum skorunu hesapla.

    Request:
        {
            "user1_id": 123,
            "user2_id": 456
        }

    Response:
        {
            "success": true,
            "data": {
                "score": 85,
                "category": "UYUMLU",
                "can_message": true,
                "reasons": [...],
                "golden_ratio_diff": 0.0234,
                "sifat_overlap": 5,
                "module_overlap": 3,
                "conflict_count": 0
            }
        }
    """

    def post(self, request):
        try:
            user1_id = _get_user_id(request)
            if not user1_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            data = json.loads(request.body)
            user2_id = data.get('user2_id')

            if not user2_id:
                return JsonResponse({'detail': 'user2_id gerekli.'}, status=400)

            if user1_id == user2_id:
                return JsonResponse({'detail': 'Cannot check compatibility with yourself.'}, status=400)

            # Profilleri al
            user1 = _get_user_profile(user1_id)
            user2 = _get_user_profile(user2_id)

            if not user1 or not user2:
                return JsonResponse({'detail': 'One of the users was not found.'}, status=404)

            # Uyum algoritmasını yükle ve hesapla
            calc_compat, _ = _load_compatibility_module()

            if not calc_compat:
                return JsonResponse({'detail': 'Compatibility module could not be loaded.'}, status=500)

            result = calc_compat(user1, user2)

            # Veritabanına kaydet (cache)
            compat_col = _get_compatibility_col()
            compat_col.update_one(
                {'user1_id': user1_id, 'user2_id': user2_id},
                {'$set': {
                    'user1_id': user1_id,
                    'user2_id': user2_id,
                    'score': result['score'],
                    'category': result['category'],
                    'can_message': result['can_message'],
                    'golden_ratio_diff': result['golden_ratio_diff'],
                    'sifat_overlap': result['sifat_overlap'],
                    'module_overlap': result['module_overlap'],
                    'conflict_count': result['conflict_count'],
                    'calculated_at': time.time()
                }},
                upsert=True
            )

            return JsonResponse({
                'success': True,
                'data': result
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        except Exception as e:
            log.exception(f'CheckCompatibility error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FindCompatibleUsersView(View):
    """
    POST /api/v1/compatibility/find/

    Bir kullanıcıya uyumlu kullanıcıları bul.

    Request:
        {
            "user_id": 123,
            "limit": 10,
            "category": "UYUMLU"  (optional)
        }

    Response:
        {
            "success": true,
            "data": [
                {
                    "user_id": 456,
                    "username": "John",
                    "score": 85,
                    "category": "UYUMLU",
                    "can_message": true,
                    "golden_ratio": 1.615,
                    "top_sifats": ["Lider", "Disiplinli", "Analitik"]
                },
                ...
            ]
        }
    """

    def post(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            data = json.loads(request.body)
            _dget = data.get
            try:
                limit = min(max(1, int(_dget('limit', 10))), 200)
            except (TypeError, ValueError):
                limit = 10
            raw_category = _dget('category')
            category_filter = raw_category if raw_category in _VALID_CATEGORIES else None

            # Kullanıcı profilini al
            user = _get_user_profile(user_id)
            if not user:
                return JsonResponse({'detail': 'User not found.'}, status=404)

            # Uyum algoritmasını yükle
            _, find_compat = _load_compatibility_module()
            if not find_compat:
                return JsonResponse({'detail': 'Compatibility module could not be loaded.'}, status=500)

            # Tüm kullanıcıları al (opsiyonel: pagination eklenebilir)
            from admin_api.utils.mongo import get_users_col
            users_col = get_users_col()
            all_users = list(users_col.find({'id': {'$ne': user_id}}, _USER_COMPAT_PROJ).limit(1000))  # Performans: ilk 1000 kullanıcı

            # Uyumlu kullanıcıları bul
            results = find_compat(user_id, [user] + all_users, category_filter, limit)

            return JsonResponse({
                'success': True,
                'data': results,
                'count': len(results)
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        except Exception as e:
            log.exception(f'FindCompatibleUsers error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CompatibilityStatsView(View):
    """
    GET /api/v1/compatibility/stats/?user_id=123

    Bir kullanıcının uyum istatistiklerini al.

    Response:
        {
            "success": true,
            "data": {
                "total_uyumlu": 42,
                "total_uyumsuz": 15,
                "total_same_category": 28,
                "total_different_category": 8,
                "avg_score": 67.5,
                "highest_score": 95,
                "lowest_score": 15
            }
        }
    """

    def get(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            compat_col = _get_compatibility_col()

            # Aggregation pipeline
            pipeline = [
                {'$match': {'$or': [{'user1_id': user_id}, {'user2_id': user_id}]}},
                {'$group': {
                    '_id': None,
                    'total_uyumlu': {'$sum': {'$cond': [{'$eq': ['$category', 'UYUMLU']}, 1, 0]}},
                    'total_uyumsuz': {'$sum': {'$cond': [{'$eq': ['$category', 'UYUMSUZ']}, 1, 0]}},
                    'total_same_category': {'$sum': {'$cond': [{'$eq': ['$category', 'SAME_CATEGORY']}, 1, 0]}},
                    'total_different_category': {'$sum': {'$cond': [{'$eq': ['$category', 'DIFFERENT_CATEGORY']}, 1, 0]}},
                    'avg_score': {'$avg': '$score'},
                    'highest_score': {'$max': '$score'},
                    'lowest_score': {'$min': '$score'},
                    'total_records': {'$sum': 1}
                }}
            ]

            stats = list(compat_col.aggregate(pipeline))

            if not stats:
                stats = [{
                    'total_uyumlu': 0,
                    'total_uyumsuz': 0,
                    'total_same_category': 0,
                    'total_different_category': 0,
                    'avg_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'total_records': 0
                }]

            return JsonResponse({
                'success': True,
                'data': stats[0]
            })

        except Exception as e:
            log.exception(f'CompatibilityStats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ListCommunitiesView(View):
    """
    GET /api/v1/communities/?type=TRAIT&limit=20

    Communityları listele.

    Query Parameters:
        type: TRAIT, MODULE, CATEGORY (optional)
        limit: Döndürülecek sonuç sayısı (default: 20)

    Response:
        {
            "success": true,
            "data": [
                {
                    "id": ObjectId,
                    "name": "Leaderboard Topluluğu",
                    "type": "TRAIT",
                    "trait_name": "Lider",
                    "member_count": 1245,
                    "description": "Lider özellikleri taşıyan kişiler...",
                    "created_at": timestamp
                },
                ...
            ]
        }
    """

    def get(self, request):
        try:
            _qget = request.GET.get
            community_type = _qget('type')
            try:
                limit = min(max(1, int(_qget('limit', 20))), 200)
            except (ValueError, TypeError):
                limit = 20

            communities_col = _get_communities_col()

            filter_dict = {}
            if community_type and community_type in _VALID_COMMUNITY_TYPES:
                filter_dict['type'] = community_type

            # Sorgu yap
            communities = list(communities_col.find(filter_dict, _COMMUNITY_LIST_PROJ).sort('member_count', -1).limit(limit))

            # ObjectId'yi string'e çevir
            for c in communities:
                _oid = c['_id']
                c['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': communities,
                'count': len(communities)
            })

        except ValueError:
            return JsonResponse({'detail': 'limit must be numeric.'}, status=400)
        except Exception as e:
            log.exception(f'ListCommunities error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class JoinCommunityView(View):
    """
    POST /api/v1/communities/<id>/join/

    Bir topluluğa katıl.

    Request:
        {
            "user_id": 123
        }

    Response:
        {
            "success": true,
            "data": {
                "community_id": ObjectId,
                "user_id": 123,
                "membership_status": "active",
                "harmony_level": 75,
                "joined_at": timestamp
            }
        }
    """

    def post(self, request, community_id=None):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            if not community_id:
                return JsonResponse({'detail': 'community_id is required.'}, status=400)

            communities_col = _get_communities_col()
            members_col = _get_community_members_col()

            # Topluluğu kontrol et
            _community_oid = None
            try:
                _community_oid = ObjectId(community_id)
                community = communities_col.find_one({'_id': _community_oid}, {'_id': 1})
            except Exception:
                community = communities_col.find_one({'_id': community_id}, {'_id': 1})

            if not community:
                return JsonResponse({'detail': 'Community not found.'}, status=404)

            # Kullanıcı profilini al (harmony score için)
            user = _get_user_profile(user_id)
            harmony_level = 75 if not user else 75  # Default harmony
            _joined_ts = time.time()

            # Üyeliği ekle — sadece yeni kayıt ise member_count artır
            upsert_result = members_col.update_one(
                {'community_id': community_id, 'user_id': user_id},
                {'$set': {
                    'community_id': community_id,
                    'user_id': user_id,
                    'harmony_level': harmony_level,
                    'is_mod': False,
                    'joined_at': _joined_ts,
                }},
                upsert=True
            )

            # Yalnızca yeni eklendiyse üye sayısını artır (duplicate upsert'te artırma)
            if upsert_result.upserted_id is not None:
                communities_col.update_one(
                    {'_id': _community_oid or community_id},
                    {'$inc': {'member_count': 1}}
                )

            return JsonResponse({
                'success': True,
                'data': {
                    'community_id': str(community_id),
                    'user_id': user_id,
                    'membership_status': 'active',
                    'harmony_level': harmony_level,
                    'joined_at': _joined_ts,
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        except Exception as e:
            log.exception(f'JoinCommunity error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ListPendingInvitationsView(View):
    """
    GET /api/v1/communities/invitations/pending/?user_id=123

    Kullanıcının bekleyen topluluk davetiyelerini listele.
    ✅ Kullanıcının onayını bekleyen davetiyeler

    Response:
        {
            "success": true,
            "data": [
                {
                    "community_id": ObjectId,
                    "community_name": "Leaderboard Topluluğu",
                    "community_type": "TRAIT",
                    "invited_at": timestamp,
                    "harmony_level": 75
                },
                ...
            ],
            "count": 5
        }
    """

    def get(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            members_col = _get_community_members_col()
            communities_col = _get_communities_col()

            # Pending davetiyeler
            pending = list(members_col.find({
                'user_id': user_id,
                'status': 'pending'
            }, _PROJ_PENDING_INVITE
            ).sort('invited_at', -1).limit(100))

            # Community bilgilerini zenginleştir — batch fetch
            raw_cids = [inv['community_id'] for inv in pending]
            oid_cids = []
            _oca = oid_cids.append
            for cid in raw_cids:
                try:
                    _oca(ObjectId(cid))
                except Exception:
                    _oca(cid)
            communities_map = {
                str(c['_id']): c
                for c in communities_col.find(
                    {'_id': {'$in': oid_cids}},
                    _PROJ_COMMUNITY_BRIEF
                )
            }
            invitations = []
            for invite in pending:
                _cid = invite['community_id']
                community = communities_map.get(str(_cid))
                if community:
                    _cget = community.get
                    _iget = invite.get
                    invitations.append({
                        'community_id': str(_cid),
                        'community_name': _cget('name', 'Unknown'),
                        'community_type': _cget('type', 'TRAIT'),
                        'trait_name': _cget('trait_name', ''),
                        'invited_at': _iget('invited_at'),
                        'harmony_level': _iget('harmony_level', 75)
                    })

            return JsonResponse({
                'success': True,
                'data': invitations,
                'count': len(invitations)
            })

        except Exception as e:
            log.exception(f'ListPendingInvitations error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ApproveCommunityInvitationView(View):
    """
    POST /api/v1/communities/{id}/approve/

    Community davetiyesini onayla veya reddet.
    ✅ Kullanıcı onayı olmadan hiçbir sohbet başlamayacak!

    Request:
        {
            "user_id": 123,
            "action": "approve" | "reject"
        }

    Response:
        {
            "success": true,
            "data": {
                "community_id": ObjectId,
                "user_id": 123,
                "status": "active" | "rejected",
                "message": "Topluluğa başarıyla katıldınız" | "Davetiye reddedildi"
            }
        }
    """

    def post(self, request, community_id=None):
        try:
            if not community_id:
                return JsonResponse({'detail': 'community_id is required.'}, status=400)

            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            _body = request.body
            data = json.loads(_body) if _body else {}
            action = data.get('action', 'approve')  # 'approve' or 'reject'

            if action not in {'approve', 'reject'}:
                return JsonResponse({'detail': 'action must be "approve" or "reject".'}, status=400)

            members_col = _get_community_members_col()
            _fau = members_col.find_one_and_update

            # Atomically claim the pending invitation (prevents double-approval race)
            if action == 'approve':
                _approve_ts = time.time()
                claimed = _fau(
                    {'community_id': community_id, 'user_id': user_id, 'status': 'pending'},
                    {'$set': {
                        'status': 'active',
                        'approved_at': _approve_ts,
                        'joined_at': _approve_ts,
                    }}
                )
            else:
                claimed = _fau(
                    {'community_id': community_id, 'user_id': user_id, 'status': 'pending'},
                    {'$set': {'status': 'rejected'}}
                )

            if not claimed:
                return JsonResponse({'detail': 'Community invitation not found.'}, status=404)

            # Davetiye onayı veya reddi
            if action == 'approve':
                # Community üye sayısını artır (claimed garantisi: yalnızca bir kez çalışır)
                communities_col = _get_communities_col()
                _cuo = communities_col.update_one
                try:
                    _cuo(
                        {'_id': ObjectId(community_id)},
                        {'$inc': {'member_count': 1}}
                    )
                except Exception:
                    _cuo(
                        {'_id': community_id},
                        {'$inc': {'member_count': 1}}
                    )

                return JsonResponse({
                    'success': True,
                    'data': {
                        'community_id': community_id,
                        'user_id': user_id,
                        'status': 'active',
                        'message': 'Successfully joined the community!'
                    }
                })

            else:  # reject
                return JsonResponse({
                    'success': True,
                    'data': {
                        'community_id': community_id,
                        'user_id': user_id,
                        'status': 'rejected',
                        'message': 'Invitation declined.'
                    }
                })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        except Exception as e:
            log.exception(f'ApproveCommunityInvitation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ListCommunityMembersView(View):
    """
    GET /api/v1/communities/<id>/members/?sort_by=harmony

    Bir topluluğun üyelerini listele.

    Query Parameters:
        sort_by: harmony, joined_at (default: harmony)
        limit: Döndürülecek üye sayısı (default: 50)

    Response:
        {
            "success": true,
            "data": [
                {
                    "user_id": 123,
                    "username": "John",
                    "harmony_level": 85,
                    "joined_at": timestamp,
                    "is_mod": false
                },
                ...
            ]
        }
    """

    def get(self, request, community_id=None):
        try:
            if not community_id:
                return JsonResponse({'detail': 'community_id is required.'}, status=400)

            _qget = request.GET.get
            sort_by = _qget('sort_by', 'harmony')
            try:
                limit = min(max(1, int(_qget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50

            members_col = _get_community_members_col()

            # Üyeleri al
            sort_field = 'harmony_level' if sort_by == 'harmony' else 'joined_at'
            members = list(members_col.find(
                {'community_id': community_id}, _MEMBER_PROJ
            ).sort(sort_field, -1).limit(limit))

            # Kullanıcı bilgilerini zenginleştir
            from admin_api.utils.mongo import get_users_col
            users_col = get_users_col()

            member_ids = [m['user_id'] for m in members]
            users_map = {u['id']: u for u in users_col.find(
                {'id': {'$in': member_ids}}, {'id': 1, 'username': 1}
            )}

            # can_request_chat: bu toplulukta aktif olan herkes chat isteği alabilir
            # (aynı toplulukta olmaları zaten yeterli)
            requesting_user_id = _get_user_id(request)
            for member in members:
                u = users_map.get(member['user_id'])
                member['username'] = u['username'] if u else 'Unknown'
                # Kendisi değilse ve toplulukta aktif üyeyse chat isteği gönderilebilir
                member['can_request_chat'] = (
                    requesting_user_id is not None
                    and member['user_id'] != requesting_user_id
                    and member.get('status', '') == 'active'
                )

            return JsonResponse({
                'success': True,
                'data': members,
                'count': len(members)
            })

        except ValueError:
            return JsonResponse({'detail': 'limit must be numeric.'}, status=400)
        except Exception as e:
            log.exception(f'ListCommunityMembers error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Subscription Helper Functions ─────────────────────────────────────────────────
import time

def _get_subscription_col():
    """user_subscriptions koleksiyonunu al"""
    return _get_db()['user_subscriptions']


def get_user_subscription(user_id: int) -> dict:
    """Kullanıcının subscription durumunu al"""
    sub_col = _get_subscription_col()

    sub = sub_col.find_one({'user_id': user_id}, _SUB_STATUS_PROJ)
    _now = time.time()

    if not sub:
        return {
            'user_id': user_id,
            'tier': 'free',
            'status': 'active',
            'created_at': _now,
        }

    # Subscription süresi doldu mu?
    if sub['tier'] == 'premium' and sub.get('renews_at', float('inf')) < _now:
        # Süresi dolmuş → free tier'a düşür
        sub_col.update_one(
            {'user_id': user_id},
            {'$set': {'tier': 'free', 'status': 'expired'}}
        )
        sub['tier'] = 'free'
        sub['status'] = 'expired'

    return sub


def count_monthly_checks(user_id: int) -> int:
    """Bu ayda yapılan compatibility check sayısını say"""
    month_ago = time.time() - (30 * 24 * 60 * 60)
    return _get_db()['compatibility'].count_documents({
        '$or': [{'user1_id': user_id}, {'user2_id': user_id}],
        'calculated_at': {'$gt': month_ago}
    })


def count_joined_communities(user_id: int) -> int:
    """Kullanıcının katıldığı topluluk sayısı (active status)"""
    return _get_db()['community_members'].count_documents({
        'user_id': user_id,
        'status': 'active'
    })


def check_free_tier_limit(user_id: int, feature: str) -> bool:
    """Free tier limitini kontrol et"""
    if feature == 'compatibility_check':
        return count_monthly_checks(user_id) < 3

    elif feature == 'community_join':
        return count_joined_communities(user_id) < 1

    elif feature == 'direct_message':
        month_ago = time.time() - (30 * 24 * 60 * 60)
        count = _get_db()['community_messages'].count_documents({
            'from_user_id': user_id,
            'created_at': {'$gt': month_ago}
        })
        return count < 10

    else:
        return True  # Bilinmeyen feature → izin ver


def require_premium_feature(feature_name):
    """Decorator: Premium feature'ı kontrol et"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            user_id = _get_user_id(request)

            if not user_id:
                # Anonim kullanıcı: devam et (ileride kontrol edilebilir)
                return view_func(self, request, *args, **kwargs)

            # Subscription kontrol et
            subscription = get_user_subscription(user_id)

            if subscription['tier'] == 'premium':
                # Premium kullanıcı: her şeye izin ver
                return view_func(self, request, *args, **kwargs)

            # Free tier: limit kontrol et
            if not check_free_tier_limit(user_id, feature_name):
                return JsonResponse({
                    'detail': f'Free tier limit reached ({feature_name})',
                    'upgrade_url': '/api/v1/subscription/upgrade/',
                    'upgrade_price': '$9.99/month'
                }, status=402)  # Payment Required

            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


# ── Subscription API Endpoints ────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionStatusView(View):
    """
    GET /api/v1/subscription/status/?user_id=123

    Kullanıcının subscription durumunu al.
    """

    def get(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            sub = get_user_subscription(user_id)
            _tier = sub['tier']

            # Kullanım bilgilerini oluştur
            usage = {
                'compatibility_checks': {
                    'used': count_monthly_checks(user_id),
                    'limit': 3 if _tier == 'free' else None
                },
                'communities_joined': {
                    'used': count_joined_communities(user_id),
                    'limit': 1 if _tier == 'free' else None
                }
            }

            _sget = sub.get
            return JsonResponse({
                'success': True,
                'data': {
                    'tier': _tier,
                    'status': _sget('status', 'active'),
                    'renews_at': _sget('renews_at'),
                    'usage': usage,
                    'features': {
                        'unlimited_messaging': _tier == 'premium',
                        'unlimited_communities': _tier == 'premium',
                        'file_sharing': _tier == 'premium'
                    }
                }
            })

        except ValueError:
            return JsonResponse({'detail': 'user_id must be numeric'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionStatus error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionUpgradeView(View):
    """
    POST /api/v1/subscription/upgrade/

    Premium'a upgrade et.
    Ödeme: Google Pay / Apple Pay (client-side).
    Vakıfbank Sanal Pos: ileriki versiyon güncellemesi ile entegre edilecek.
    """

    def post(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            data = json.loads(request.body)
            billing_cycle = data.get('billing_cycle', 'monthly')
            if billing_cycle not in ('monthly', 'yearly'):
                billing_cycle = 'monthly'

            price_try = '199.99 TRY/ay' if billing_cycle == 'monthly' else '1699 TRY/yıl'

            return JsonResponse({
                'success': True,
                'data': {
                    'payment_methods': ['google_pay', 'apple_pay'],
                    'price': price_try,
                    'billing_cycle': billing_cycle,
                    'message': 'Ödeme Google Pay veya Apple Pay ile tamamlanır.'
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionUpgrade error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionCancelView(View):
    """
    POST /api/v1/subscription/cancel/

    Subscription'ı iptal et.
    """

    def post(self, request):
        try:
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            sub_col = _get_subscription_col()

            sub_col.update_one(
                {'user_id': user_id},
                {'$set': {
                    'tier': 'free',
                    'status': 'cancelled',
                    'ended_at': time.time()
                }}
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'message': 'Subscription iptal edildi',
                    'tier': 'free',
                    'status': 'cancelled'
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionCancel error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
