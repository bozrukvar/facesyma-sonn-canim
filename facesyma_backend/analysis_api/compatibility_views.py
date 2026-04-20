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
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from django.conf import settings
import sys
from pathlib import Path

log = logging.getLogger(__name__)


# ── JWT yardımcısı ────────────────────────────────────────────────────────────
def _get_user_id(request) -> int | None:
    """Token'dan user_id çıkar. Token yoksa None döner."""
    import jwt
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(
            auth.split(' ', 1)[1], settings.JWT_SECRET, algorithms=['HS256']
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


# ── Compatibility Algorithm ───────────────────────────────────────────────────
def _load_compatibility_module():
    """compatibility.py modülünü yükle"""
    engine_path = settings.FACESYMA_ENGINE_PATH
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)

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
    user = users_col.find_one({'id': user_id}, {
        '_id': 0, 'id': 1, 'username': 1, 'golden_ratio': 1,
        'top_sifats': 1, 'modules': 1
    })

    if not user:
        return None

    # Eksik alanlar için defaults
    user.setdefault('golden_ratio', 1.618)
    user.setdefault('top_sifats', [])
    user.setdefault('modules', [])

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
            data = json.loads(request.body)
            user1_id = data.get('user1_id')
            user2_id = data.get('user2_id')

            if not user1_id or not user2_id:
                return JsonResponse({'detail': 'user1_id ve user2_id gerekli.'}, status=400)

            if user1_id == user2_id:
                return JsonResponse({'detail': 'Aynı kullanıcıyla uyum kontrol edilemez.'}, status=400)

            # Profilleri al
            user1 = _get_user_profile(user1_id)
            user2 = _get_user_profile(user2_id)

            if not user1 or not user2:
                return JsonResponse({'detail': 'Kullanıcılardan biri bulunamadı.'}, status=404)

            # Uyum algoritmasını yükle ve hesapla
            calc_compat, _ = _load_compatibility_module()

            if not calc_compat:
                return JsonResponse({'detail': 'Compatibility modülü yüklenemedı.'}, status=500)

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
                    'calculated_at': __import__('time').time()
                }},
                upsert=True
            )

            return JsonResponse({
                'success': True,
                'data': result
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Geçersiz JSON.'}, status=400)
        except Exception as e:
            log.exception(f'CheckCompatibility hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
            data = json.loads(request.body)
            user_id = data.get('user_id')
            limit = data.get('limit', 10)
            category_filter = data.get('category')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli.'}, status=400)

            # Kullanıcı profilini al
            user = _get_user_profile(user_id)
            if not user:
                return JsonResponse({'detail': 'Kullanıcı bulunamadı.'}, status=404)

            # Uyum algoritmasını yükle
            _, find_compat = _load_compatibility_module()
            if not find_compat:
                return JsonResponse({'detail': 'Compatibility modülü yüklenemedı.'}, status=500)

            # Tüm kullanıcıları al (opsiyonel: pagination eklenebilir)
            from admin_api.utils.mongo import get_users_col
            users_col = get_users_col()
            all_users = list(users_col.find({'id': {'$ne': user_id}}, {
                '_id': 0, 'id': 1, 'username': 1, 'golden_ratio': 1,
                'top_sifats': 1, 'modules': 1
            }).limit(1000))  # Performans: ilk 1000 kullanıcı

            # Uyumlu kullanıcıları bul
            results = find_compat(user_id, [user] + all_users, category_filter, limit)

            return JsonResponse({
                'success': True,
                'data': results,
                'count': len(results)
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Geçersiz JSON.'}, status=400)
        except Exception as e:
            log.exception(f'FindCompatibleUsers hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli.'}, status=400)

            try:
                user_id = int(user_id)
            except ValueError:
                return JsonResponse({'detail': 'user_id sayısal olmalıdır.'}, status=400)

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
            log.exception(f'CompatibilityStats hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ListCommunitiesView(View):
    """
    GET /api/v1/communities/?type=TRAIT&limit=20

    Toplulukları listele.

    Query Parameters:
        type: TRAIT, MODULE, CATEGORY (optional)
        limit: Döndürülecek sonuç sayısı (default: 20)

    Response:
        {
            "success": true,
            "data": [
                {
                    "id": ObjectId,
                    "name": "Liderlik Topluluğu",
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
            community_type = request.GET.get('type')
            limit = int(request.GET.get('limit', 20))

            communities_col = _get_communities_col()

            # Filter oluştur
            filter_dict = {}
            if community_type:
                filter_dict['type'] = community_type

            # Sorgu yap
            communities = list(communities_col.find(filter_dict, {
                '_id': 1, 'name': 1, 'type': 1, 'trait_name': 1,
                'member_count': 1, 'description': 1, 'created_at': 1,
                'is_active': 1
            }).sort('member_count', -1).limit(limit))

            # ObjectId'yi string'e çevir
            for c in communities:
                c['_id'] = str(c['_id'])

            return JsonResponse({
                'success': True,
                'data': communities,
                'count': len(communities)
            })

        except ValueError:
            return JsonResponse({'detail': 'limit sayısal olmalıdır.'}, status=400)
        except Exception as e:
            log.exception(f'ListCommunities hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
            if not community_id:
                return JsonResponse({'detail': 'community_id gerekli.'}, status=400)

            data = json.loads(request.body) if request.body else {}
            user_id = data.get('user_id')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli.'}, status=400)

            communities_col = _get_communities_col()
            members_col = _get_community_members_col()

            # Topluluğu kontrol et
            try:
                from bson import ObjectId
                community = communities_col.find_one({'_id': ObjectId(community_id)})
            except:
                community = communities_col.find_one({'_id': community_id})

            if not community:
                return JsonResponse({'detail': 'Topluluk bulunamadı.'}, status=404)

            # Kullanıcı profilini al (harmony score için)
            user = _get_user_profile(user_id)
            harmony_level = 75 if not user else 75  # Default harmony

            # Üyeliği ekle (duplicate olursa update et)
            import time
            members_col.update_one(
                {'community_id': community_id, 'user_id': user_id},
                {'$set': {
                    'community_id': community_id,
                    'user_id': user_id,
                    'harmony_level': harmony_level,
                    'is_mod': False,
                    'joined_at': time.time()
                }},
                upsert=True
            )

            # Topluluk üye sayısını artır
            communities_col.update_one(
                {'_id': community_id if isinstance(community_id, str) else ObjectId(community_id)},
                {'$inc': {'member_count': 1}}
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'community_id': str(community_id),
                    'user_id': user_id,
                    'membership_status': 'active',
                    'harmony_level': harmony_level,
                    'joined_at': __import__('time').time()
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Geçersiz JSON.'}, status=400)
        except Exception as e:
            log.exception(f'JoinCommunity hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
                    "community_name": "Liderlik Topluluğu",
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
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli.'}, status=400)

            try:
                user_id = int(user_id)
            except ValueError:
                return JsonResponse({'detail': 'user_id sayısal olmalıdır.'}, status=400)

            members_col = _get_community_members_col()
            communities_col = _get_communities_col()

            # Pending davetiyeler
            pending = list(members_col.find({
                'user_id': user_id,
                'status': 'pending'
            }).sort('invited_at', -1))

            # Topluluk bilgilerini zenginleştir
            invitations = []
            for invite in pending:
                try:
                    from bson import ObjectId
                    community = communities_col.find_one({'_id': ObjectId(invite['community_id'])})
                except:
                    community = communities_col.find_one({'_id': invite['community_id']})

                if community:
                    invitations.append({
                        'community_id': str(invite['community_id']),
                        'community_name': community.get('name', 'Unknown'),
                        'community_type': community.get('type', 'TRAIT'),
                        'trait_name': community.get('trait_name', ''),
                        'invited_at': invite.get('invited_at'),
                        'harmony_level': invite.get('harmony_level', 75)
                    })

            return JsonResponse({
                'success': True,
                'data': invitations,
                'count': len(invitations)
            })

        except Exception as e:
            log.exception(f'ListPendingInvitations hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ApproveCommunityInvitationView(View):
    """
    POST /api/v1/communities/{id}/approve/

    Topluluk davetiyesini onayla veya reddet.
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
                return JsonResponse({'detail': 'community_id gerekli.'}, status=400)

            data = json.loads(request.body) if request.body else {}
            user_id = data.get('user_id')
            action = data.get('action', 'approve')  # 'approve' or 'reject'

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli.'}, status=400)

            if action not in ['approve', 'reject']:
                return JsonResponse({'detail': 'action "approve" veya "reject" olmalıdır.'}, status=400)

            members_col = _get_community_members_col()

            # Pending davetiye bul
            invitation = members_col.find_one({
                'community_id': community_id,
                'user_id': user_id,
                'status': 'pending'
            })

            if not invitation:
                return JsonResponse({'detail': 'Topluluk davetiyesi bulunamadı.'}, status=404)

            # Davetiye onayı veya reddi
            if action == 'approve':
                # ✅ Kullanıcı davetiyeyi kabul etti
                members_col.update_one(
                    {'community_id': community_id, 'user_id': user_id},
                    {'$set': {
                        'status': 'active',
                        'approved_at': __import__('time').time(),
                        'joined_at': __import__('time').time()
                    }}
                )

                # Topluluk üye sayısını artır
                communities_col = _get_communities_col()
                try:
                    from bson import ObjectId
                    communities_col.update_one(
                        {'_id': ObjectId(community_id)},
                        {'$inc': {'member_count': 1}}
                    )
                except:
                    communities_col.update_one(
                        {'_id': community_id},
                        {'$inc': {'member_count': 1}}
                    )

                return JsonResponse({
                    'success': True,
                    'data': {
                        'community_id': community_id,
                        'user_id': user_id,
                        'status': 'active',
                        'message': 'Topluluğa başarıyla katıldınız!'
                    }
                })

            else:  # reject
                # ❌ Kullanıcı davetiyeyi reddetti
                members_col.update_one(
                    {'community_id': community_id, 'user_id': user_id},
                    {'$set': {'status': 'rejected'}}
                )

                return JsonResponse({
                    'success': True,
                    'data': {
                        'community_id': community_id,
                        'user_id': user_id,
                        'status': 'rejected',
                        'message': 'Davetiye reddedildi.'
                    }
                })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Geçersiz JSON.'}, status=400)
        except Exception as e:
            log.exception(f'ApproveCommunityInvitation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


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
                return JsonResponse({'detail': 'community_id gerekli.'}, status=400)

            sort_by = request.GET.get('sort_by', 'harmony')
            limit = int(request.GET.get('limit', 50))

            members_col = _get_community_members_col()

            # Üyeleri al
            sort_field = 'harmony_level' if sort_by == 'harmony' else 'joined_at'
            members = list(members_col.find({'community_id': community_id}, {
                '_id': 0, 'user_id': 1, 'harmony_level': 1,
                'joined_at': 1, 'is_mod': 1
            }).sort(sort_field, -1).limit(limit))

            # Kullanıcı bilgilerini zenginleştir
            from admin_api.utils.mongo import get_users_col
            users_col = get_users_col()

            for member in members:
                user = users_col.find_one({'id': member['user_id']}, {'username': 1})
                member['username'] = user['username'] if user else 'Unknown'

            return JsonResponse({
                'success': True,
                'data': members,
                'count': len(members)
            })

        except ValueError:
            return JsonResponse({'detail': 'limit sayısal olmalıdır.'}, status=400)
        except Exception as e:
            log.exception(f'ListCommunityMembers hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Subscription Helper Functions ─────────────────────────────────────────────────
import time

def _get_subscription_col():
    """user_subscriptions koleksiyonunu al"""
    return _get_db()['user_subscriptions']


def get_user_subscription(user_id: int) -> dict:
    """Kullanıcının subscription durumunu al"""
    sub_col = _get_subscription_col()

    sub = sub_col.find_one({'user_id': user_id})

    if not sub:
        # Yeni kullanıcı → varsayılan olarak free tier
        return {
            'user_id': user_id,
            'tier': 'free',
            'status': 'active',
            'created_at': time.time()
        }

    # Subscription süresi doldu mu?
    if sub['tier'] == 'premium' and sub.get('renews_at', float('inf')) < time.time():
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
    compat_col = _get_db()['compatibility']

    now = time.time()
    month_ago = now - (30 * 24 * 60 * 60)

    count = compat_col.count_documents({
        '$or': [
            {'user1_id': user_id},
            {'user2_id': user_id}
        ],
        'calculated_at': {'$gt': month_ago}
    })

    return count


def count_joined_communities(user_id: int) -> int:
    """Kullanıcının katıldığı topluluk sayısı (active status)"""
    members_col = _get_db()['community_members']

    count = members_col.count_documents({
        'user_id': user_id,
        'status': 'active'
    })

    return count


def check_free_tier_limit(user_id: int, feature: str) -> bool:
    """Free tier limitini kontrol et"""

    if feature == 'compatibility_check':
        return count_monthly_checks(user_id) < 3

    elif feature == 'community_join':
        return count_joined_communities(user_id) < 1

    elif feature == 'direct_message':
        # Ay içinde gönderilen mesaj sayısını say
        messages_col = _get_db()['community_messages']
        now = time.time()
        month_ago = now - (30 * 24 * 60 * 60)

        count = messages_col.count_documents({
            'from_user_id': user_id,
            'created_at': {'$gt': month_ago}
        })

        return count < 10

    else:
        return True  # Bilinmeyen feature → izin ver


def require_premium_feature(feature_name):
    """Decorator: Premium feature'ı kontrol et"""
    def decorator(view_func):
        from functools import wraps
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
                    'detail': f'Free tier limitine ulaştınız ({feature_name})',
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
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({'detail': 'user_id parametresi gerekli'}, status=400)

            user_id = int(user_id)
            sub = get_user_subscription(user_id)

            # Kullanım bilgilerini oluştur
            usage = {
                'compatibility_checks': {
                    'used': count_monthly_checks(user_id),
                    'limit': 3 if sub['tier'] == 'free' else None
                },
                'communities_joined': {
                    'used': count_joined_communities(user_id),
                    'limit': 1 if sub['tier'] == 'free' else None
                }
            }

            return JsonResponse({
                'success': True,
                'data': {
                    'tier': sub['tier'],
                    'status': sub.get('status', 'active'),
                    'renews_at': sub.get('renews_at'),
                    'usage': usage,
                    'features': {
                        'unlimited_messaging': sub['tier'] == 'premium',
                        'unlimited_communities': sub['tier'] == 'premium',
                        'file_sharing': sub['tier'] == 'premium'
                    }
                }
            })

        except ValueError:
            return JsonResponse({'detail': 'user_id sayısal olmalıdır'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionStatus hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionUpgradeView(View):
    """
    POST /api/v1/subscription/upgrade/

    Premium'a upgrade et. Şimdilik mock checkout döner.
    İleride Stripe/iyzico entegrasyonu yapılacak.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            billing_cycle = data.get('billing_cycle', 'monthly')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli'}, status=400)

            # TODO: Stripe/iyzico entegrasyonu
            # Şimdi: mock checkout URL döner

            price = '$9.99/month' if billing_cycle == 'monthly' else '$89/year'

            return JsonResponse({
                'success': True,
                'data': {
                    'checkout_url': 'https://checkout.stripe.com/pay/mock_session_' + str(user_id),
                    'price': price,
                    'billing_cycle': billing_cycle,
                    'message': 'Ödeme sayfasına yönlendirileceksiniz'
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Geçersiz JSON'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionUpgrade hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionCancelView(View):
    """
    POST /api/v1/subscription/cancel/

    Subscription'ı iptal et.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')

            if not user_id:
                return JsonResponse({'detail': 'user_id gerekli'}, status=400)

            sub_col = _get_subscription_col()

            sub_col.update_one(
                {'user_id': int(user_id)},
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
            return JsonResponse({'detail': 'Geçersiz JSON'}, status=400)
        except Exception as e:
            log.exception(f'SubscriptionCancel hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
