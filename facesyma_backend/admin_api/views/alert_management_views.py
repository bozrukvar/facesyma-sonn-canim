"""
admin_api/views/alert_management_views.py
==========================================
Alert rules management — CRUD operations for automated alert rules.
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import _get_db, _next_id

log = logging.getLogger(__name__)


def _json(request):
    """Parse request body JSON"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


@method_decorator(csrf_exempt, name='dispatch')
class AlertRulesListView(View):
    """
    GET /api/v1/admin/alerts/rules/ — List all alert rules
    POST /api/v1/admin/alerts/rules/ — Create new rule

    POST Body:
    {
      "name": "...",
      "description": "...",
      "metric": "new_users_today|analyses_today|error_rate_1h|active_users_5min",
      "condition": "less_than|greater_than",
      "threshold": N,
      "enabled": true,
      "cooldown_minutes": 60,
      "notify_email": "admin@example.com"
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
            rules_col = _get_db()['alert_rules']
            rules = list(rules_col.find({}, {'_id': 0}, sort=[('id', 1)]))
            return JsonResponse({'rules': rules})
        except Exception as e:
            log.exception(f'Alert rules list error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = _json(request)
            rules_col = _get_db()['alert_rules']

            # Validate required fields
            required = ['name', 'metric', 'condition', 'threshold']
            if not all(f in data for f in required):
                return JsonResponse({'detail': 'Missing required fields'}, status=400)

            rule = {
                'id': _next_id(rules_col),
                'name': data['name'],
                'description': data.get('description', ''),
                'metric': data['metric'],
                'condition': data['condition'],
                'threshold': data['threshold'],
                'enabled': data.get('enabled', True),
                'cooldown_minutes': data.get('cooldown_minutes', 60),
                'notify_email': data.get('notify_email', ''),
                'slack_webhook_url': data.get('slack_webhook_url', ''),  # YENİ
                'last_triggered_at': None,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }

            rules_col.insert_one(rule)
            rule.pop('_id', None)
            return JsonResponse({'rule': rule, 'message': 'Rule created'})

        except Exception as e:
            log.exception(f'Alert rule creation error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertRuleDetailView(View):
    """
    PATCH /api/v1/admin/alerts/rules/<int:rule_id>/ — Update rule
    DELETE /api/v1/admin/alerts/rules/<int:rule_id>/ — Delete rule
    """

    def patch(self, request, rule_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = _json(request)
            rules_col = _get_db()['alert_rules']

            update_ops = {'updated_at': datetime.utcnow().isoformat()}

            # Allowlist of updatable fields
            for field in ['name', 'description', 'enabled', 'cooldown_minutes', 'notify_email', 'slack_webhook_url']:  # YENİ
                if field in data:
                    update_ops[field] = data[field]

            if update_ops == {'updated_at': update_ops['updated_at']}:
                return JsonResponse({'detail': 'No updates provided'}, status=400)

            rules_col.update_one({'id': rule_id}, {'$set': update_ops})
            rule = rules_col.find_one({'id': rule_id}, {'_id': 0})

            return JsonResponse({'rule': rule, 'message': 'Rule updated'})

        except Exception as e:
            log.exception(f'Alert rule update error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def delete(self, request, rule_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            rules_col = _get_db()['alert_rules']
            result = rules_col.delete_one({'id': rule_id})

            if result.deleted_count == 0:
                return JsonResponse({'detail': 'Rule not found'}, status=404)

            return JsonResponse({'message': 'Rule deleted'})

        except Exception as e:
            log.exception(f'Alert rule delete error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertHistoryListView(View):
    """
    GET /api/v1/admin/alerts/history/ — List alert trigger history
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            history_col = _get_db()['alert_history']

            # Pagination
            page = int(request.GET.get('page', 1))
            limit = min(int(request.GET.get('limit', 20)), 100)
            skip = (page - 1) * limit

            total = history_col.count_documents({})
            items = list(history_col.find(
                {}, {'_id': 0},
                sort=[('triggered_at', -1)],
                skip=skip,
                limit=limit
            ))

            return JsonResponse({
                'items': items,
                'total': total,
                'page': page,
                'limit': limit,
            })

        except Exception as e:
            log.exception(f'Alert history list error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertStatsView(View):
    """
    GET /api/v1/admin/alerts/stats/ — Alert rule statistics
    """

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            rules_col = _get_db()['alert_rules']
            history_col = _get_db()['alert_history']

            # Total and enabled rules
            total_rules = rules_col.count_documents({})
            enabled_rules = rules_col.count_documents({'enabled': True})

            # Triggered this week
            week_ago = (datetime.utcnow() - __import__('datetime').timedelta(days=7)).isoformat()
            week_triggers = history_col.count_documents({
                'triggered_at': {'$gte': week_ago}
            })

            # Emails sent
            emails_sent = history_col.count_documents({'email_sent': True})

            return JsonResponse({
                'total_rules': total_rules,
                'enabled_rules': enabled_rules,
                'triggered_this_week': week_triggers,
                'emails_sent': emails_sent,
            })

        except Exception as e:
            log.exception(f'Alert stats error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
