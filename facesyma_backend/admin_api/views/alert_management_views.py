"""
admin_api/views/alert_management_views.py
==========================================
Alert rules management — CRUD operations for automated alert rules.
"""

import json
import logging
import math as _math
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin
from admin_api.utils.mongo import _get_db, _next_id

log = logging.getLogger(__name__)

_VALID_ALERT_METRICS    = frozenset({'new_users_today', 'analyses_today', 'error_rate_1h', 'active_users_5min'})
_VALID_ALERT_CONDITIONS = frozenset({'less_than', 'greater_than'})


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
            rules = list(rules_col.find({}, {'_id': 0}, sort=[('id', 1)]).limit(500))
            return JsonResponse({'rules': rules})
        except Exception as e:
            log.exception(f'Alert rules list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = _json(request)
            _dget = data.get
            _now = datetime.utcnow()
            rules_col = _get_db()['alert_rules']

            # Validate required fields
            required = ['name', 'metric', 'condition', 'threshold']
            if not all(f in data for f in required):
                return JsonResponse({'detail': 'Missing required fields'}, status=400)



            _dmetric = data['metric']; _dcond = data['condition']
            if _dmetric not in _VALID_ALERT_METRICS:
                return JsonResponse({'detail': f'Invalid metric. Allowed: {", ".join(sorted(_VALID_ALERT_METRICS))}'}, status=400)
            if _dcond not in _VALID_ALERT_CONDITIONS:
                return JsonResponse({'detail': 'Invalid condition. Allowed: less_than, greater_than'}, status=400)
            try:
                threshold = float(data['threshold'])
            except (TypeError, ValueError):
                return JsonResponse({'detail': 'Threshold must be a number.'}, status=400)
            if _math.isnan(threshold) or _math.isinf(threshold):
                return JsonResponse({'detail': 'Threshold must be a finite number.'}, status=400)

            try:
                cooldown = max(1, min(int(_dget('cooldown_minutes', 60)), 10080))
            except (TypeError, ValueError):
                cooldown = 60

            _now_iso = _now.isoformat()
            rule = {
                'id': _next_id(rules_col),
                'name': str(data['name'])[:100],
                'description': str(_dget('description', ''))[:500],
                'metric': _dmetric,
                'condition': _dcond,
                'threshold': threshold,
                'enabled': bool(_dget('enabled', True)),
                'cooldown_minutes': cooldown,
                'notify_email': str(_dget('notify_email', ''))[:254],
                'slack_webhook_url': str(_dget('slack_webhook_url', ''))[:512],
                'last_triggered_at': None,
                'created_at': _now_iso,
                'updated_at': _now_iso,
            }

            rules_col.insert_one(rule)
            rule.pop('_id', None)
            return JsonResponse({'rule': rule, 'message': 'Rule created'})

        except Exception as e:
            log.exception(f'Alert rule creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


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

            update_ops = {'updated_at': datetime.utcnow().isoformat()}  # single call, patch path

            # Allowlist of updatable fields with sanitization
            if 'name' in data:
                update_ops['name'] = str(data['name'])[:100]
            if 'description' in data:
                update_ops['description'] = str(data['description'])[:500]
            if 'enabled' in data:
                update_ops['enabled'] = bool(data['enabled'])
            if 'cooldown_minutes' in data:
                try:
                    update_ops['cooldown_minutes'] = max(1, min(int(data['cooldown_minutes']), 10080))
                except (TypeError, ValueError):
                    return JsonResponse({'detail': 'cooldown_minutes must be an integer.'}, status=400)


            if 'metric' in data:
                _dm = data['metric']
                if _dm not in _VALID_ALERT_METRICS:
                    return JsonResponse({'detail': f'Invalid metric. Allowed: {", ".join(sorted(_VALID_ALERT_METRICS))}'}, status=400)
                update_ops['metric'] = _dm
            if 'condition' in data:
                _dc = data['condition']
                if _dc not in _VALID_ALERT_CONDITIONS:
                    return JsonResponse({'detail': 'Invalid condition. Allowed: less_than, greater_than'}, status=400)
                update_ops['condition'] = _dc
            if 'threshold' in data:
                try:
                    thr = float(data['threshold'])
                except (TypeError, ValueError):
                    return JsonResponse({'detail': 'Threshold must be a number.'}, status=400)
                if _math.isnan(thr) or _math.isinf(thr):
                    return JsonResponse({'detail': 'Threshold must be a finite number.'}, status=400)
                update_ops['threshold'] = thr
            if 'notify_email' in data:
                update_ops['notify_email'] = str(data['notify_email'])[:254]
            if 'slack_webhook_url' in data:
                update_ops['slack_webhook_url'] = str(data['slack_webhook_url'])[:512]

            if update_ops == {'updated_at': update_ops['updated_at']}:
                return JsonResponse({'detail': 'No updates provided'}, status=400)

            rules_col.update_one({'id': rule_id}, {'$set': update_ops})
            rule = rules_col.find_one({'id': rule_id}, {'_id': 0})
            if not rule:
                return JsonResponse({'detail': 'Rule not found after update.'}, status=404)

            return JsonResponse({'rule': rule, 'message': 'Rule updated'})

        except Exception as e:
            log.exception(f'Alert rule update error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

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
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


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
            _qget = request.GET.get
            try:
                page = max(1, int(_qget('page', 1)))
                limit = min(max(1, int(_qget('limit', 20))), 100)
            except (ValueError, TypeError):
                page, limit = 1, 20
            skip = (page - 1) * limit

            total = history_col.estimated_document_count()
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
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


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
            _db = _get_db()
            rules_col = _db['alert_rules']
            history_col = _db['alert_history']

            # Rules: total + enabled (single $facet)
            _rf = next(rules_col.aggregate([{'$facet': {
                'total':   [{'$count': 'n'}],
                'enabled': [{'$match': {'enabled': True}}, {'$count': 'n'}],
            }}]), {})
            _rfget = _rf.get
            total_rules   = (_rfget('total',   [{}])[0] or {}).get('n', 0)
            enabled_rules = (_rfget('enabled', [{}])[0] or {}).get('n', 0)

            # History: week triggers + emails sent (single $facet)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            _hf = next(history_col.aggregate([{'$facet': {
                'week':   [{'$match': {'triggered_at': {'$gte': week_ago}}}, {'$count': 'n'}],
                'emails': [{'$match': {'email_sent': True}}, {'$count': 'n'}],
            }}]), {})
            _hfget = _hf.get
            week_triggers = (_hfget('week',   [{}])[0] or {}).get('n', 0)
            emails_sent   = (_hfget('emails', [{}])[0] or {}).get('n', 0)

            return JsonResponse({
                'total_rules': total_rules,
                'enabled_rules': enabled_rules,
                'triggered_this_week': week_triggers,
                'emails_sent': emails_sent,
            })

        except Exception as e:
            log.exception(f'Alert stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
