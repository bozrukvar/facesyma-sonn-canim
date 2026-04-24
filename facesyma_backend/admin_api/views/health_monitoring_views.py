"""
admin_api/views/health_monitoring_views.py
==========================================
Advanced Health Monitoring & Alert Management
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_VALID_ALERT_SEVERITIES = frozenset({'low', 'medium', 'high', 'critical'})


@method_decorator(csrf_exempt, name='dispatch')
class HealthMonitoringView(View):
    """Detaylı sağlık izleme"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            health_col = db['service_health']
            metrics_col = db['service_metrics']

            services = ['django', 'fastapi-chat', 'coach-service', 'mongodb']
            now = datetime.utcnow()
            check_window = now - timedelta(minutes=5)

            # Single aggregation: latest health check per service (4 → 1 query)
            latest_checks = {
                doc['_id']: doc
                for doc in health_col.aggregate([
                    {'$match': {'service': {'$in': services}, 'timestamp': {'$gte': check_window}}},
                    {'$sort': {'timestamp': -1}},
                    {'$group': {
                        '_id': '$service',
                        'status':             {'$first': '$status'},
                        'response_time_ms':   {'$first': '$response_time_ms'},
                        'timestamp':          {'$first': '$timestamp'},
                        'uptime_percentage':  {'$first': '$uptime_percentage'},
                    }},
                ])
            }

            service_status = {}
            for service in services:
                check = latest_checks.get(service)
                if check:
                    _chget = check.get
                    ts = _chget('timestamp', now)
                    service_status[service] = {
                        'status': _chget('status', 'unknown'),
                        'response_time_ms': _chget('response_time_ms', 0),
                        'last_check': ts.isoformat() if isinstance(ts, datetime) else str(ts),
                        'uptime_percentage': _chget('uptime_percentage', 100)
                    }
                else:
                    service_status[service] = {
                        'status': 'unknown',
                        'response_time_ms': 0,
                        'last_check': 'never',
                        'uptime_percentage': 0
                    }

            # Batch fetch latest metric per service in a single aggregation
            metrics_agg = metrics_col.aggregate([
                {'$match': {'service': {'$in': list(services)}}},
                {'$sort': {'timestamp': -1}},
                {'$group': {'_id': '$service',
                            'cpu_usage':    {'$first': '$cpu_usage'},
                            'memory_usage': {'$first': '$memory_usage'},
                            'disk_usage':   {'$first': '$disk_usage'},
                            'connections':  {'$first': '$connections'}}},
            ])
            metrics = {
                doc['_id']: {
                    'cpu_usage':    (_dg := doc.get)('cpu_usage', 0),
                    'memory_usage': _dg('memory_usage', 0),
                    'disk_usage':   _dg('disk_usage', 0),
                    'connections':  _dg('connections', 0),
                }
                for doc in metrics_agg
            }

            overall_status = 'healthy' if all(
                s['status'] == 'healthy' for s in service_status.values()
            ) else 'degraded'

            return JsonResponse({
                'success': True,
                'data': {
                    'overall_status': overall_status,
                    'services': service_status,
                    'metrics': metrics,
                    'timestamp': now.isoformat()
                }
            })

        except Exception as e:
            log.exception(f'Health monitoring error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertConfigView(View):
    """Alert kuralları - yapılandırma"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            alert_col = db['alert_rules']

            rules = list(alert_col.find({}, {'_id': 0}).limit(500))

            return JsonResponse({
                'success': True,
                'data': {
                    'total_rules': len(rules),
                    'active_rules': sum(1 for r in rules if r.get('enabled', True)),
                    'rules': rules
                }
            })

        except Exception as e:
            log.exception(f'Alert config get error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        try:
            admin_payload = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            db = _get_db()
            alert_col = db['alert_rules']

            rule = {
                'name': str(_dget('name', ''))[:100],
                'condition': str(_dget('condition', ''))[:200],
                'threshold': _dget('threshold'),
                'metric': str(_dget('metric', ''))[:50],
                'enabled': bool(_dget('enabled', True)),
                'severity': str(_dget('severity', 'medium'))[:20],
                'notification_channels': _dget('notification_channels', ['email', 'slack']),
                'created_at': datetime.utcnow(),
                'created_by': admin_payload.get('email', 'admin')
            }

            result = alert_col.insert_one(rule)
            _rname = rule['name']
            log.info(f"Alert rule created: {_rname}")

            return JsonResponse({
                'success': True,
                'data': {
                    'rule_id': str(result.inserted_id),
                    'name': _rname,
                    'severity': rule['severity']
                }
            })

        except Exception as e:
            log.exception(f'Alert rule creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertHistoryView(View):
    """Alert geçmişi ve istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            history_col = db['alert_history']

            _qget = request.GET.get
            try:
                days = min(max(1, int(_qget('days', 30))), 365)
                limit = min(max(1, int(_qget('limit', 100))), 500)
            except (ValueError, TypeError):
                days = 30
                limit = 100

            severity = _qget('severity')
            start_date = datetime.utcnow() - timedelta(days=days)


            query = {'timestamp': {'$gte': start_date}}
            if severity and severity in _VALID_ALERT_SEVERITIES:
                query['severity'] = severity

            alerts = list(history_col.find(query).sort('timestamp', -1).limit(limit))
            for a in alerts:
                _oid = a['_id']
                a['_id'] = str(_oid)
                _ts = a.get('timestamp')
                if isinstance(_ts, datetime):
                    a['timestamp'] = _ts.isoformat()

            _hf = next(history_col.aggregate([{'$facet': {
                'total':    [{'$match': query},                                                             {'$count': 'n'}],
                'low':      [{'$match': {'severity': 'low',      'timestamp': {'$gte': start_date}}},      {'$count': 'n'}],
                'medium':   [{'$match': {'severity': 'medium',   'timestamp': {'$gte': start_date}}},      {'$count': 'n'}],
                'high':     [{'$match': {'severity': 'high',     'timestamp': {'$gte': start_date}}},      {'$count': 'n'}],
                'critical': [{'$match': {'severity': 'critical', 'timestamp': {'$gte': start_date}}},      {'$count': 'n'}],
                'resolved': [
                    {'$match': {'resolved_at': {'$exists': True}, 'timestamp': {'$gte': start_date}}},
                    {'$project': {'resolution_time': {'$subtract': ['$resolved_at', '$timestamp']}}},
                    {'$group': {'_id': None, 'avg': {'$avg': '$resolution_time'}}},
                ],
            }}]), {})
            _hfget = _hf.get
            total_alerts = (_hfget('total', [{}])[0] or {}).get('n', 0)
            stats = {sev: (_hfget(sev, [{}])[0] or {}).get('n', 0) for sev in _VALID_ALERT_SEVERITIES}
            _avg_ms = (_hfget('resolved', [{}])[0] or {}).get('avg', 0) or 0
            avg_resolution_time = _avg_ms / 3600

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': days,
                    'total_alerts': total_alerts,
                    'severity_breakdown': stats,
                    'avg_resolution_time_hours': round(avg_resolution_time, 2),
                    'recent_alerts': alerts
                }
            })

        except Exception as e:
            log.exception(f'Alert history error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
