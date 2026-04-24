"""
admin_api/views/audit_log_views.py
==================================
Admin activity audit log API endpoints.
"""

import json
import logging
import re as _re
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import _get_db

log = logging.getLogger(__name__)

_RE_EMAIL_FILTER  = _re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_RE_ACTION_FILTER = _re.compile(r'^[a-zA-Z0-9_.]{1,100}$')
_RE_TARGET_FILTER = _re.compile(r'^[a-zA-Z0-9_]{1,50}$')


def _json(request):
    """Parse request body JSON"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


@method_decorator(csrf_exempt, name='dispatch')
class AuditLogListView(View):
    """
    GET /api/v1/admin/audit/logs/

    List admin activity logs with optional filtering.

    Query Params:
        - admin_id: Filter by admin user ID
        - admin_email: Filter by admin email
        - action: Filter by action type
        - target_type: Filter by target type (user, app_config, sifat, etc.)
        - from_date: ISO string — logs from this date onwards
        - to_date: ISO string — logs until this date
        - page: Page number (1-indexed, default 1)
        - limit: Results per page (default 20, max 100)

    Response:
    {
      "logs": [...],
      "total": N,
      "page": N,
      "limit": N
    }
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            audit_col = _get_db()['admin_activity_log']

            # Build filter query
            query = {}

            _qp = request.GET
            _qpget = _qp.get
            admin_id = _qpget('admin_id')
            if admin_id:
                try:
                    query['admin_id'] = int(admin_id)
                except ValueError:
                    pass

            admin_email = _qpget('admin_email', '')[:254]
            if admin_email and _RE_EMAIL_FILTER.match(admin_email):
                query['admin_email'] = admin_email

            action = _qpget('action', '')
            if action and _RE_ACTION_FILTER.match(action):
                query['action'] = action

            target_type = _qpget('target_type', '')
            if target_type and _RE_TARGET_FILTER.match(target_type):
                query['target_type'] = target_type

            from_date = _qpget('from_date')
            to_date = _qpget('to_date')
            if from_date or to_date:
                date_query = {}
                try:
                    if from_date:
                        date_query['$gte'] = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                    if to_date:
                        date_query['$lt'] = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return JsonResponse({'detail': 'Invalid date format. Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).'}, status=400)
                if date_query:
                    query['timestamp'] = date_query

            # Pagination
            try:
                page = max(1, int(_qpget('page', 1)))
                limit = min(max(1, int(_qpget('limit', 20))), 100)
            except (ValueError, TypeError):
                page, limit = 1, 20
            skip = (page - 1) * limit

            # Count total
            total = audit_col.count_documents(query)

            # Fetch logs
            logs = list(audit_col.find(
                query,
                {'_id': 0},
                sort=[('timestamp', -1)],
                skip=skip,
                limit=limit
            ))

            return JsonResponse({
                'logs': logs,
                'total': total,
                'page': page,
                'limit': limit,
            })

        except Exception as e:
            log.exception(f'Audit log list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AuditLogStatsView(View):
    """
    GET /api/v1/admin/audit/stats/

    Get audit log statistics (aggregated analytics).

    Response:
    {
      "total_actions": N,
      "today_actions": N,
      "this_week_actions": N,
      "unique_admins": N,
      "action_breakdown": {
        "action_type": count,
        ...
      },
      "top_admins": [
        {"admin_email": "...", "actions": N},
        ...
      ]
    }
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            audit_col = _get_db()['admin_activity_log']

            now = datetime.utcnow()
            today_iso = datetime(now.year, now.month, now.day).isoformat()
            week_ago_iso = (now - timedelta(days=7)).isoformat()

            _af = next(audit_col.aggregate([{'$facet': {
                'total':      [{'$count': 'n'}],
                'today':      [{'$match': {'timestamp': {'$gte': today_iso}}},    {'$count': 'n'}],
                'week':       [{'$match': {'timestamp': {'$gte': week_ago_iso}}}, {'$count': 'n'}],
                'by_action':  [{'$group': {'_id': '$action',     'count': {'$sum': 1}}}, {'$sort': {'count': -1}}],
                'top_admins': [{'$group': {'_id': '$admin_email', 'actions': {'$sum': 1}}}, {'$sort': {'actions': -1}}, {'$limit': 10}],
                'unique_adm': [{'$group': {'_id': '$admin_id'}}],
            }}]), {})
            _afget = _af.get
            total_actions  = (_afget('total', [{}])[0] or {}).get('n', 0)
            today_actions  = (_afget('today', [{}])[0] or {}).get('n', 0)
            week_actions   = (_afget('week',  [{}])[0] or {}).get('n', 0)
            unique_admins  = len(_afget('unique_adm', []))
            action_breakdown = {doc['_id']: doc['count'] for doc in _afget('by_action', [])}
            top_admins = [
                {'admin_email': doc['_id'], 'actions': doc['actions']}
                for doc in _afget('top_admins', [])
            ]

            return JsonResponse({
                'total_actions': total_actions,
                'today_actions': today_actions,
                'this_week_actions': week_actions,
                'unique_admins': unique_admins,
                'action_breakdown': action_breakdown,
                'top_admins': top_admins,
            })

        except Exception as e:
            log.exception(f'Audit stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
