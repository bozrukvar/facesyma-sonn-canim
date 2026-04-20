"""
admin_api/views/audit_log_views.py
==================================
Admin activity audit log API endpoints.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import _get_db

log = logging.getLogger(__name__)


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

            admin_id = request.GET.get('admin_id')
            if admin_id:
                try:
                    query['admin_id'] = int(admin_id)
                except ValueError:
                    pass

            admin_email = request.GET.get('admin_email')
            if admin_email:
                query['admin_email'] = admin_email

            action = request.GET.get('action')
            if action:
                query['action'] = action

            target_type = request.GET.get('target_type')
            if target_type:
                query['target_type'] = target_type

            from_date = request.GET.get('from_date')
            to_date = request.GET.get('to_date')
            if from_date or to_date:
                date_query = {}
                if from_date:
                    date_query['$gte'] = from_date
                if to_date:
                    date_query['$lt'] = to_date
                if date_query:
                    query['timestamp'] = date_query

            # Pagination
            page = int(request.GET.get('page', 1))
            limit = min(int(request.GET.get('limit', 20)), 100)
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
            return JsonResponse({'detail': str(e)}, status=500)


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
            week_ago_iso = (now - __import__('datetime').timedelta(days=7)).isoformat()

            # Total actions
            total_actions = audit_col.count_documents({})

            # Today actions
            today_actions = audit_col.count_documents({
                'timestamp': {'$gte': today_iso}
            })

            # This week actions
            week_actions = audit_col.count_documents({
                'timestamp': {'$gte': week_ago_iso}
            })

            # Unique admins
            unique_admins = len(audit_col.distinct('admin_id', {}))

            # Action breakdown
            action_pipeline = [
                {'$group': {'_id': '$action', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            action_breakdown = {
                doc['_id']: doc['count']
                for doc in audit_col.aggregate(action_pipeline)
            }

            # Top admins
            top_admins_pipeline = [
                {'$group': {
                    '_id': '$admin_email',
                    'actions': {'$sum': 1}
                }},
                {'$sort': {'actions': -1}},
                {'$limit': 10}
            ]
            top_admins = [
                {'admin_email': doc['_id'], 'actions': doc['actions']}
                for doc in audit_col.aggregate(top_admins_pipeline)
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
            return JsonResponse({'detail': str(e)}, status=500)
