"""
admin_api/views/user_views.py
==============================
Kullanıcı yönetimi endpoint'leri (CRUD + istatistikler).
"""

import json
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_history_col, get_plan_log_col, _next_id
from admin_api.utils.audit import log_admin_action, extract_ip


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _user_dict(user: dict) -> dict:
    """Kullanıcı dokümanını response formatına dönüştür"""
    return {
        'id': user.get('id'),
        'email': user.get('email'),
        'username': user.get('username'),
        'avatar': user.get('avatar'),
        'plan': user.get('plan', 'free'),
        'auth_method': user.get('auth_method'),
        'is_active': user.get('is_active'),
        'created_at': str(user.get('date_joined', '')),
        'google_id': user.get('google_id'),  # Opsiyonel
        'app_source': user.get('app_source', 'mobile'),  # YENİ
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ── Kullanıcı Listesi ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserListView(View):
    """
    Tüm kullanıcıları listele (sayfalanmış, filtreleme, arama).

    GET /api/v1/admin/users/?page=1&limit=20&plan=premium&search=email&app_source=web
    Query params:
        - page: int (default 1)
        - limit: int (default 20, max 100)
        - plan: str ("free" | "premium" | diğer)
        - search: str (email veya username'de arama)
        - sort: str ("date_joined" | "-date_joined" | "plan")
        - app_source: str ("web" | "mobile" | boş = tüm kaynaklar)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # Query params
        page = max(1, int(request.GET.get('page', 1)))
        limit = min(int(request.GET.get('limit', 20)), 100)  # Max 100
        plan_filter = request.GET.get('plan', None)
        search = request.GET.get('search', '').strip().lower()
        sort = request.GET.get('sort', '-date_joined')
        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)
        app_source = request.GET.get('app_source', None)

        # MongoDB query
        col = get_users_col()
        query = {}

        # App source filtresi (mobile/web)
        if app_source == 'mobile':
            query['$or'] = [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}]
        elif app_source == 'web':
            query['app_source'] = 'web'

        # Plan filtresi
        if plan_filter:
            query['plan'] = plan_filter

        # Arama
        if search:
            query['$or'] = [
                {'email': {'$regex': search, '$options': 'i'}},
                {'username': {'$regex': search, '$options': 'i'}},
            ]

        # Tarih aralığı filtresi
        if from_date:
            query.setdefault('date_joined', {})
            query['date_joined']['$gte'] = from_date
        if to_date:
            query.setdefault('date_joined', {})
            query['date_joined']['$lt'] = to_date + 'T23:59:59'

        # Sort mapping
        sort_map = {
            'date_joined': [('date_joined', 1)],
            '-date_joined': [('date_joined', -1)],
            'plan': [('plan', 1)],
            '-plan': [('plan', -1)],
        }
        sort_spec = sort_map.get(sort, [('date_joined', -1)])

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        users = list(
            col.find(query, {'password': 0})  # Şifre gönderme
            .sort(sort_spec)
            .skip(skip)
            .limit(limit)
        )

        return JsonResponse({
            'users': [_user_dict(u) for u in users],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,  # Ceil division
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Kullanıcı İstatistikleri ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserStatsView(View):
    """
    Kullanıcı istatistikleri.

    GET /api/v1/admin/users/stats/
    Return: {
        total_users,
        by_plan: {free, premium, ...},
        by_auth_method: {email, google},
        active_users,
        inactive_users,
        registered_today,
        registered_this_week
    }
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        col = get_users_col()

        # Toplam kullanıcı
        total = col.count_documents({})

        # Plan dağılımı
        plan_stats = col.aggregate([
            {'$group': {'_id': '$plan', 'count': {'$sum': 1}}},
        ])
        plan_dict = {doc['_id'] or 'free': doc['count'] for doc in plan_stats}

        # Auth metodu dağılımı
        auth_stats = col.aggregate([
            {'$group': {'_id': '$auth_method', 'count': {'$sum': 1}}},
        ])
        auth_dict = {doc['_id']: doc['count'] for doc in auth_stats}

        # Aktif/pasif
        active = col.count_documents({'is_active': True})
        inactive = col.count_documents({'is_active': False})

        # Bugün kaydolanlar
        import time
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        today_iso = today_start.isoformat()

        registered_today = col.count_documents({
            'date_joined': {'$gte': today_iso}
        })

        # Bu haftada kaydolanlar
        week_ago = datetime.fromtimestamp(
            datetime.now().timestamp() - (7 * 86400)
        ).isoformat()
        registered_week = col.count_documents({
            'date_joined': {'$gte': week_ago}
        })

        # App source dağılımı
        web_users = col.count_documents({'app_source': 'web'})
        mobile_users = col.count_documents({'$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}]})

        return JsonResponse({
            'total_users': total,
            'by_plan': plan_dict,
            'by_auth_method': auth_dict,
            'by_app_source': {'mobile': mobile_users, 'web': web_users},  # YENİ
            'active_users': active,
            'inactive_users': inactive,
            'registered_today': registered_today,
            'registered_this_week': registered_week,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Kullanıcı Detayı ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserDetailView(View):
    """
    Tek kullanıcının detayı + analiz geçmişi.

    GET /api/v1/admin/users/<uid>/
    Return: {user, recent_history: [{mode, lang, result, created_at}, ...]}
    """

    def get(self, request, uid):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        # Kullanıcıyı bul
        users_col = get_users_col()
        user = users_col.find_one({'id': int(uid)})

        if not user:
            return JsonResponse(
                {'detail': 'Kullanıcı bulunamadı.'},
                status=404
            )

        # Son 10 analiz
        history_col = get_history_col()
        history = list(
            history_col.find(
                {'user_id': int(uid)},
                {'_id': 0}
            )
            .sort([('created_at', -1)])
            .limit(10)
        )

        return JsonResponse({
            'user': _user_dict(user),
            'recent_history': history,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Kullanıcı Güncelle ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserUpdateView(View):
    """
    Kullanıcı güncellemeleri (plan, is_active).

    PATCH /api/v1/admin/users/<uid>/
    Body: {plan?, is_active?}
    """

    def patch(self, request, uid):
        try:
            admin = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        data = _json(request)
        users_col = get_users_col()

        # Kullanıcıyı bul
        user = users_col.find_one({'id': int(uid)})
        if not user:
            return JsonResponse(
                {'detail': 'Kullanıcı bulunamadı.'},
                status=404
            )

        # Güncellenebilir alanlar
        update_data = {}
        old_plan = user.get('plan')

        if 'plan' in data:
            update_data['plan'] = data['plan']
        if 'is_active' in data:
            update_data['is_active'] = bool(data['is_active'])

        if not update_data:
            return JsonResponse(
                {'detail': 'Güncellenecek alan yok.'},
                status=400
            )

        # Güncelle
        users_col.update_one({'id': int(uid)}, {'$set': update_data})

        # Audit log
        log_admin_action(
            admin, 'update_user', 'user', int(uid),
            old_value=user, new_value=update_data,
            ip_address=extract_ip(request)
        )

        # Plan değişikliğini log'la
        if 'plan' in update_data:
            log_col = get_plan_log_col()
            log_id = _next_id(log_col)
            log_col.insert_one({
                'id': log_id,
                'user_id': int(uid),
                'user_email': user.get('email'),
                'old_plan': old_plan,
                'new_plan': update_data['plan'],
                'changed_by_admin_id': admin['admin_id'],
                'changed_at': datetime.now().isoformat(),
                'note': f"Admin tarafından değiştirildi ({admin['email']})"
            })

        # Güncellenmiş kullanıcıyı döner
        updated_user = users_col.find_one({'id': int(uid)})
        return JsonResponse({
            'message': 'Kullanıcı güncellendi.',
            'user': _user_dict(updated_user)
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Kullanıcı Sil ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserDeleteView(View):
    """
    Kullanıcıyı sil (ve analiz geçmişini).

    DELETE /api/v1/admin/users/<uid>/
    Return: {message}
    """

    def delete(self, request, uid):
        try:
            admin = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        users_col = get_users_col()
        history_col = get_history_col()

        # Kullanıcı var mı?
        user = users_col.find_one({'id': int(uid)})
        if not user:
            return JsonResponse(
                {'detail': 'Kullanıcı bulunamadı.'},
                status=404
            )

        # Sil: kullanıcı + analiz geçmişi
        users_col.delete_one({'id': int(uid)})
        history_col.delete_many({'user_id': int(uid)})

        # Audit log
        log_admin_action(
            admin, 'delete_user', 'user', int(uid),
            old_value=user, new_value=None,
            ip_address=extract_ip(request),
            detail=f"Email: {user.get('email')}"
        )

        return JsonResponse({
            'message': f'Kullanıcı silindi: {user.get("email")}'
        })
