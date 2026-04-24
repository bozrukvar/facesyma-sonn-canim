"""
admin_api/views/user_views.py
==============================
Kullanıcı yönetimi endpoint'leri (CRUD + istatistikler).
"""

import json
import re
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


_USER_LIST_PROJECTION = {
    '_id': 0, 'id': 1, 'email': 1, 'username': 1, 'avatar': 1,
    'plan': 1, 'auth_method': 1, 'is_active': 1, 'date_joined': 1,
    'google_id': 1, 'app_source': 1,
}
_VALID_USER_PLANS = frozenset({'free', 'premium', 'tier_a', 'tier_b', 'tier_c', 'tier_d'})
_USER_SORT_MAP: dict = {
    'date_joined':  [('date_joined', 1)],
    '-date_joined': [('date_joined', -1)],
    'plan':         [('plan', 1)],
    '-plan':        [('plan', -1)],
}


def _user_dict(user: dict) -> dict:
    """Kullanıcı dokümanını response formatına dönüştür"""
    _uget = user.get
    return {
        'id': _uget('id'),
        'email': _uget('email'),
        'username': _uget('username'),
        'avatar': _uget('avatar'),
        'plan': _uget('plan', 'free'),
        'auth_method': _uget('auth_method'),
        'is_active': _uget('is_active'),
        'created_at': str(_uget('date_joined', '')),
        'google_id': _uget('google_id'),
        'app_source': _uget('app_source', 'mobile'),
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

        _qp = request.GET
        _qpget = _qp.get
        try:
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20
        plan_filter = _qpget('plan', None)
        if plan_filter and plan_filter not in _VALID_USER_PLANS:
            plan_filter = None
        search = _qpget('search', '').strip().lower()
        sort = _qpget('sort', '-date_joined')
        from_date = _qpget('from_date', None)
        to_date = _qpget('to_date', None)
        app_source = _qpget('app_source', None)

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
            safe_search = re.escape(search)
            search_or = [
                {'email': {'$regex': safe_search, '$options': 'i'}},
                {'username': {'$regex': safe_search, '$options': 'i'}},
            ]
            if '$or' in query:
                # Combine existing $or (app_source) with search $or using $and
                query['$and'] = [{'$or': query.pop('$or')}, {'$or': search_or}]
            else:
                query['$or'] = search_or

        # Tarih aralığı filtresi
        if from_date or to_date:
            _dj = query.setdefault('date_joined', {})
            if from_date:
                _dj['$gte'] = from_date
            if to_date:
                _dj['$lt'] = to_date + 'T23:59:59'

        sort_spec = _USER_SORT_MAP.get(sort, [('date_joined', -1)])

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        users = list(
            col.find(query, _USER_LIST_PROJECTION)
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
# ── Kullanıcı Statleri ──────────────────────────────────────────────────
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

        now = datetime.utcnow()
        today_iso = datetime(now.year, now.month, now.day).isoformat()
        week_ago  = datetime.fromtimestamp(now.timestamp() - 7 * 86400).isoformat()

        _s = next(col.aggregate([{'$facet': {
            'total':    [{'$count': 'n'}],
            'active':   [{'$match': {'is_active': True}},  {'$count': 'n'}],
            'inactive': [{'$match': {'is_active': False}}, {'$count': 'n'}],
            'today':    [{'$match': {'date_joined': {'$gte': today_iso}}}, {'$count': 'n'}],
            'week':     [{'$match': {'date_joined': {'$gte': week_ago}}},  {'$count': 'n'}],
            'web':      [{'$match': {'app_source': 'web'}}, {'$count': 'n'}],
            'mobile':   [{'$match': {'$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}]}}, {'$count': 'n'}],
            'by_plan':  [{'$group': {'_id': '$plan',        'count': {'$sum': 1}}}],
            'by_auth':  [{'$group': {'_id': '$auth_method', 'count': {'$sum': 1}}}],
        }}]), {})
        _sget = _s.get
        total            = (_sget('total',    [{}])[0] or {}).get('n', 0)
        active           = (_sget('active',   [{}])[0] or {}).get('n', 0)
        inactive         = (_sget('inactive', [{}])[0] or {}).get('n', 0)
        registered_today = (_sget('today',    [{}])[0] or {}).get('n', 0)
        registered_week  = (_sget('week',     [{}])[0] or {}).get('n', 0)
        web_users        = (_sget('web',      [{}])[0] or {}).get('n', 0)
        mobile_users     = (_sget('mobile',   [{}])[0] or {}).get('n', 0)
        plan_dict        = {doc['_id'] or 'free': doc['count'] for doc in _sget('by_plan', [])}
        auth_dict        = {doc['_id']: doc['count']           for doc in _sget('by_auth', [])}

        return JsonResponse({
            'total_users': total,
            'by_plan': plan_dict,
            'by_auth_method': auth_dict,
            'by_app_source': {'mobile': mobile_users, 'web': web_users},
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
        _uid = int(uid)
        users_col = get_users_col()
        user = users_col.find_one({'id': _uid}, _USER_LIST_PROJECTION)

        if not user:
            return JsonResponse(
                {'detail': 'User not found.'},
                status=404
            )

        # Son 10 analiz
        history_col = get_history_col()
        history = list(
            history_col.find(
                {'user_id': _uid},
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
        _uid = int(uid)
        users_col = get_users_col()
        _fo = users_col.find_one

        # Kullanıcıyı bul
        user = _fo({'id': _uid}, {'_id': 0, 'plan': 1, 'email': 1})
        if not user:
            return JsonResponse(
                {'detail': 'User not found.'},
                status=404
            )

        # Güncellenebilir alanlar
        update_data = {}
        _uget = user.get
        old_plan = _uget('plan')

        if 'plan' in data:
            _new_plan = data['plan']
            update_data['plan'] = _new_plan
        if 'is_active' in data:
            update_data['is_active'] = bool(data['is_active'])

        if not update_data:
            return JsonResponse(
                {'detail': 'No fields to update.'},
                status=400
            )

        # Güncelle
        users_col.update_one({'id': _uid}, {'$set': update_data})

        # Audit log
        log_admin_action(
            admin, 'update_user', 'user', _uid,
            old_value=user, new_value=update_data,
            ip_address=extract_ip(request)
        )

        # Plan değişikliğini log'la
        if 'plan' in update_data:
            log_col = get_plan_log_col()
            log_id = _next_id(log_col)
            log_col.insert_one({
                'id': log_id,
                'user_id': _uid,
                'user_email': _uget('email'),
                'old_plan': old_plan,
                'new_plan': _new_plan,
                'changed_by_admin_id': admin['admin_id'],
                'changed_at': datetime.utcnow().isoformat(),
                'note': f"Admin tarafından değiştirildi ({admin['email']})"
            })

        # Güncellenmiş kullanıcıyı döner
        updated_user = _fo({'id': _uid}, _USER_LIST_PROJECTION)
        if not updated_user:
            return JsonResponse({'detail': 'User not found after update.'}, status=404)
        return JsonResponse({
            'message': 'User updated.',
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

        _uid = int(uid)
        users_col = get_users_col()
        history_col = get_history_col()

        # Kullanıcı var mı?
        user = users_col.find_one({'id': _uid}, {'_id': 1})
        if not user:
            return JsonResponse(
                {'detail': 'User not found.'},
                status=404
            )

        # Sil: kullanıcı + analiz geçmişi
        users_col.delete_one({'id': _uid})
        history_col.delete_many({'user_id': _uid})

        # Audit log
        _user_email = user.get('email')
        log_admin_action(
            admin, 'delete_user', 'user', _uid,
            old_value=user, new_value=None,
            ip_address=extract_ip(request),
            detail=f"Email: {_user_email}"
        )

        return JsonResponse({
            'message': f'User deleted: {_user_email}'
        })
