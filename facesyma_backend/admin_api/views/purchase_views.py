"""
admin_api/views/purchase_views.py
==================================
Premium kullanıcılar ve plan takibi.
"""

import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import get_users_col, get_plan_log_col


_VALID_PURCHASE_PLANS  = frozenset({'free', 'premium', 'tier_a', 'tier_b', 'tier_c', 'tier_d'})
_PREMIUM_USER_PROJ     = {'_id': 0, 'id': 1, 'email': 1, 'username': 1, 'date_joined': 1, 'auth_method': 1}


def _json(request):
    """Request body JSON'ı parse et"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ── Premium Kullanıcı Listesi ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class PremiumListView(View):
    """
    Premium plan kullanıcılarını listele (sayfalanmış).

    GET /api/v1/admin/purchases/premium/?page=1&limit=20
    Query params:
        - page: int (default 1)
        - limit: int (default 20, max 100)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 20))), 100)
        except (ValueError, TypeError):
            page, limit = 1, 20

        col = get_users_col()

        # Premium sorgusu
        total = col.count_documents({'plan': 'premium'})
        skip = (page - 1) * limit

        users = list(
            col.find({'plan': 'premium'}, _PREMIUM_USER_PROJ)
            .sort([('date_joined', -1)])
            .skip(skip)
            .limit(limit)
        )

        return JsonResponse({
            'premium_users': [
                {
                    'id': (_ug := u.get)('id'),
                    'email': _ug('email'),
                    'username': _ug('username'),
                    'joined_at': str(_ug('date_joined', '')),
                    'auth_method': _ug('auth_method'),
                }
                for u in users
            ],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Plan Statleri ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class PurchaseStatsView(View):
    """
    Plan satın alma istatistikleri.

    GET /api/v1/admin/purchases/stats/
    Return: {
        total_plans,
        by_plan: {free, premium, ...},
        premium_revenue_estimate,
        premium_count,
        churn_rate_estimate
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

        _pf = next(col.aggregate([{'$facet': {
            'total':            [{'$count': 'n'}],
            'inactive_premium': [{'$match': {'plan': 'premium', 'is_active': False}}, {'$count': 'n'}],
            'by_plan':          [{'$group': {'_id': '$plan', 'count': {'$sum': 1}}}],
        }}]), {})
        _pfget = _pf.get
        total            = (_pfget('total',            [{}])[0] or {}).get('n', 0)
        inactive_premium = (_pfget('inactive_premium', [{}])[0] or {}).get('n', 0)
        plan_dict        = {doc['_id'] or 'free': doc['count'] for doc in _pfget('by_plan', [])}

        _pdget = plan_dict.get
        premium_count = _pdget('premium', 0)
        free_count = _pdget('free', 0)

        estimated_monthly_revenue = premium_count * 9.99
        churn_rate = (inactive_premium / premium_count * 100) if premium_count > 0 else 0

        return JsonResponse({
            'total_users': total,
            'by_plan': plan_dict,
            'premium_count': premium_count,
            'free_count': free_count,
            'premium_percentage': round((premium_count / total * 100) if total > 0 else 0, 2),
            'estimated_monthly_revenue': round(estimated_monthly_revenue, 2),
            'churn_rate': round(churn_rate, 2),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# ── Plan Değişim Geçmişi ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class PlanChangeLogView(View):
    """
    Plan değişikliklerinin geçmişi (sayfalanmış).

    GET /api/v1/admin/purchases/log/?page=1&limit=50&user_id=42
    Query params:
        - page: int (default 1)
        - limit: int (default 50, max 200)
        - user_id: int (opsiyonel, belirli kullanıcıya filtre)
        - plan: str (opsiyonel, "premium" veya "free" filtresi)
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qp = request.GET
            _qpget = _qp.get
            page = max(1, int(_qpget('page', 1)))
            limit = min(max(1, int(_qpget('limit', 50))), 200)
        except (ValueError, TypeError):
            page, limit = 1, 50
        user_id = _qpget('user_id', None)
        plan = _qpget('plan', None)

        if plan and plan not in _VALID_PURCHASE_PLANS:
            plan = None

        col = get_plan_log_col()

        # Query
        query = {}
        if user_id:
            try:
                query['user_id'] = int(user_id)
            except (ValueError, TypeError):
                return JsonResponse({'detail': 'user_id must be an integer.'}, status=400)
        if plan:
            query['new_plan'] = plan

        # Total count
        total = col.count_documents(query)

        # Sayfalanmış sorgu
        skip = (page - 1) * limit
        logs = list(
            col.find(query, {'_id': 0})
            .sort([('changed_at', -1)])
            .skip(skip)
            .limit(limit)
        )

        return JsonResponse({
            'logs': logs,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit,
            }
        })
