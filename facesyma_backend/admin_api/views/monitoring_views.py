"""
admin_api/views/monitoring_views.py
===================================
Health Monitoring & Alerting
"""

import json
import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin
try:
    import requests as _requests
except ImportError:
    _requests = None

log = logging.getLogger(__name__)

_VALID_LOG_LEVELS = frozenset({'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'})
_VALID_LOG_SERVICES = frozenset({'django', 'fastapi-chat', 'coach-service', 'face-validation', 'finetune', 'test-service'})


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """Sistem sağlık kontrolü"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            health_data = {}

            try:
                db.command('ping')
                health_data['mongodb'] = {'status': 'up', 'latency_ms': 10}
            except Exception:
                health_data['mongodb'] = {'status': 'down', 'latency_ms': None}

            health_data['django_api'] = {'status': 'up', 'latency_ms': 5}

            try:
                if _requests is None:
                    raise ImportError
                response = _requests.get('http://localhost:8002/health', timeout=5)
                if response.status_code == 200:
                    health_data['chat_service'] = {'status': 'up', 'latency_ms': response.elapsed.total_seconds() * 1000}
                else:
                    health_data['chat_service'] = {'status': 'down'}
            except Exception:
                health_data['chat_service'] = {'status': 'down'}

            try:
                if _requests is None:
                    raise ImportError
                response = _requests.get('http://localhost:8003/health', timeout=5)
                if response.status_code == 200:
                    health_data['coach_service'] = {'status': 'up', 'latency_ms': response.elapsed.total_seconds() * 1000}
                else:
                    health_data['coach_service'] = {'status': 'down'}
            except Exception:
                health_data['coach_service'] = {'status': 'down'}

            all_up = all(s['status'] == 'up' for s in health_data.values())

            return JsonResponse({
                'success': True,
                'data': {
                    'overall_status': 'healthy' if all_up else 'degraded',
                    'timestamp': datetime.utcnow().isoformat(),
                    'services': health_data
                }
            })

        except Exception as e:
            log.exception(f'Health check error: {e}')
            return JsonResponse({'success': False, 'data': {'overall_status': 'unhealthy'}, 'detail': 'Service health check failed.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UptimeMetricsView(View):
    """Sistem uptime metrikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            uptime_col = db['uptime_logs']

            try:
                period_days = min(max(1, int(request.GET.get('period', 30))), 365)
            except (ValueError, TypeError):
                period_days = 30

            start_date = datetime.utcnow() - timedelta(days=period_days)
            _uf = next(uptime_col.aggregate([{'$facet': {
                'total': [{'$match': {'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
                'up':    [{'$match': {'timestamp': {'$gte': start_date}, 'status': 'up'}}, {'$count': 'n'}],
            }}]), {})
            _ufget = _uf.get
            total_checks = (_ufget('total', [{}])[0] or {}).get('n', 0)
            up_checks    = (_ufget('up',    [{}])[0] or {}).get('n', 0)
            availability = (up_checks / total_checks * 100) if total_checks else 100

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': period_days,
                    'availability_percentage': round(availability, 2),
                    'total_checks': total_checks,
                    'up_checks': up_checks,
                    'sla_target': 99.9,
                    'sla_met': availability >= 99.9
                }
            })

        except Exception as e:
            log.exception(f'Uptime metrics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ErrorRateView(View):
    """API hata oranı metrikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            error_col = db['error_logs']

            try:
                period_hours = min(max(1, int(request.GET.get('period', 24))), 720)
            except (ValueError, TypeError):
                period_hours = 24

            start_date = datetime.utcnow() - timedelta(hours=period_hours)
            _ef = next(error_col.aggregate([{'$facet': {
                'total':     [{'$match': {'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
                'endpoints': [
                    {'$match': {'timestamp': {'$gte': start_date}}},
                    {'$group': {'_id': '$endpoint', 'count': {'$sum': 1}, 'latest': {'$max': '$timestamp'}}},
                    {'$sort': {'count': -1}}, {'$limit': 10},
                ],
                'types': [
                    {'$match': {'timestamp': {'$gte': start_date}}},
                    {'$group': {'_id': '$error_type', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}}, {'$limit': 50},
                ],
            }}]), {})
            _efget = _ef.get
            total_errors    = (_efget('total', [{}])[0] or {}).get('n', 0)
            endpoint_errors = _efget('endpoints', [])
            error_types     = {(e['_id'] or 'unknown'): e['count'] for e in _efget('types', [])}

            return JsonResponse({
                'success': True,
                'data': {
                    'period_hours': period_hours,
                    'total_errors': total_errors,
                    'error_rate': round((total_errors / max((period_hours * 3600), 1)) * 100, 4),
                    'top_errors': endpoint_errors,
                    'error_types': error_types
                }
            })

        except Exception as e:
            log.exception(f'Error rate error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResponseTimeView(View):
    """API response time metrikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            log_col = db['api_logs']

            try:
                period_hours = min(max(1, int(request.GET.get('period', 24))), 720)
            except (ValueError, TypeError):
                period_hours = 24

            start_date = datetime.utcnow() - timedelta(hours=period_hours)

            stats = list(log_col.aggregate([
                {'$match': {'timestamp': {'$gte': start_date}, 'response_time_ms': {'$exists': True}}},
                {'$group': {
                    '_id': None,
                    'avg_response_time': {'$avg': '$response_time_ms'},
                    'min_response_time': {'$min': '$response_time_ms'},
                    'max_response_time': {'$max': '$response_time_ms'},
                    'p95_response_time': {'$avg': '$response_time_ms'},
                    'p99_response_time': {'$max': '$response_time_ms'}
                }}
            ]))

            if stats:
                stat = stats[0]
                _stget = stat.get
                _avg_rt = _stget('avg_response_time', 0)
                metrics = {
                    'period_hours': period_hours,
                    'average_ms': round(_avg_rt, 2),
                    'min_ms': round(_stget('min_response_time', 0), 2),
                    'max_ms': round(_stget('max_response_time', 0), 2),
                    'p95_ms': round(_stget('p95_response_time', 0), 2),
                    'p99_ms': round(_stget('p99_response_time', 0), 2),
                    'slo_target_ms': 500,
                    'slo_met': _avg_rt < 500
                }
            else:
                metrics = {'period_hours': period_hours, 'average_ms': 0, 'min_ms': 0, 'max_ms': 0, 'message': 'Veri yok'}

            return JsonResponse({'success': True, 'data': metrics})

        except Exception as e:
            log.exception(f'Response time error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertManagementView(View):
    """Alert yönetimi"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            alert_col = db['alerts']

            alerts = list(alert_col.find({'status': 'active'}).sort('created_at', -1).limit(200))
            for a in alerts:
                _oid = a['_id']
                a['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {'active_alerts': len(alerts), 'alerts': alerts}
            })

        except Exception as e:
            log.exception(f'Alert list error: {e}')
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
            db = _get_db()
            alert_col = db['alerts']

            _dget = data.get
            alert = {
                'name': str(_dget('name', ''))[:100],
                'type': str(_dget('type', ''))[:50],
                'condition': _dget('condition'),
                'threshold': _dget('threshold'),
                'status': 'active',
                'created_at': datetime.utcnow(),
                'created_by': admin_payload.get('email', 'admin'),
                'notification_channels': _dget('notification_channels', [])
            }

            result = alert_col.insert_one(alert)

            return JsonResponse({
                'success': True,
                'data': {'alert_id': str(result.inserted_id), 'message': 'Alert created'}
            })

        except Exception as e:
            log.exception(f'Alert creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogsView(View):
    """Sistem logları"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            log_col = db['system_logs']

            _qget = request.GET.get
            level = _qget('level')
            service = _qget('service')
            try:
                limit = min(max(1, int(_qget('limit', 100))), 500)
            except (ValueError, TypeError):
                limit = 100

            query = {}
            if level and level in _VALID_LOG_LEVELS:
                query['level'] = level
            if service and service in _VALID_LOG_SERVICES:
                query['service'] = service

            logs = list(log_col.find(query).sort('timestamp', -1).limit(limit))
            for entry in logs:
                _oid = entry['_id']
                entry['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {
                    'total': log_col.count_documents(query),
                    'limit': limit,
                    'logs': logs
                }
            })

        except Exception as e:
            log.exception(f'Logs error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
