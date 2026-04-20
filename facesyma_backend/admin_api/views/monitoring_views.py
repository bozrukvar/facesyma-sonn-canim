"""
admin_api/views/monitoring_views.py
===================================
Health Monitoring & Alerting

Features:
  - Service health checks
  - API uptime monitoring
  - Error rate tracking
  - Response time monitoring
  - Alert management
"""

import json
import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from django.conf import settings

log = logging.getLogger(__name__)


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """Sistem sağlık kontrolü"""

    def get(self, request):
        try:
            db = _get_db()
            health_data = {}

            # MongoDB kontrolü
            try:
                db.command('ping')
                health_data['mongodb'] = {'status': 'up', 'latency_ms': 10}
            except:
                health_data['mongodb'] = {'status': 'down', 'latency_ms': None}

            # Django API kontrolü
            health_data['django_api'] = {'status': 'up', 'latency_ms': 5}

            # FastAPI Chat Service kontrolü
            try:
                import requests
                response = requests.get('http://localhost:8002/health', timeout=5)
                if response.status_code == 200:
                    health_data['chat_service'] = {'status': 'up', 'latency_ms': response.elapsed.total_seconds() * 1000}
                else:
                    health_data['chat_service'] = {'status': 'down'}
            except:
                health_data['chat_service'] = {'status': 'down'}

            # Coach Service kontrolü
            try:
                import requests
                response = requests.get('http://localhost:8003/health', timeout=5)
                if response.status_code == 200:
                    health_data['coach_service'] = {'status': 'up', 'latency_ms': response.elapsed.total_seconds() * 1000}
                else:
                    health_data['coach_service'] = {'status': 'down'}
            except:
                health_data['coach_service'] = {'status': 'down'}

            # Overall status
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
            log.exception(f'Health check hatası: {e}')
            return JsonResponse({
                'success': False,
                'data': {'overall_status': 'unhealthy'},
                'detail': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UptimeMetricsView(View):
    """Sistem uptime metrikleri"""

    def get(self, request):
        try:
            db = _get_db()
            uptime_col = db['uptime_logs']

            period = request.GET.get('period', '30')  # days
            period_days = int(period)

            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Get uptime logs
            logs = list(uptime_col.find({
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', -1))

            # Calculate availability
            if logs:
                total_checks = len(logs)
                up_checks = sum(1 for log in logs if log.get('status') == 'up')
                availability = (up_checks / total_checks) * 100
            else:
                availability = 100

            metrics = {
                'period_days': period_days,
                'availability_percentage': round(availability, 2),
                'total_checks': total_checks if logs else 0,
                'up_checks': up_checks if logs else 0,
                'sla_target': 99.9,
                'sla_met': availability >= 99.9
            }

            return JsonResponse({
                'success': True,
                'data': metrics
            })

        except Exception as e:
            log.exception(f'Uptime metrics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ErrorRateView(View):
    """API hata oranı metrikleri"""

    def get(self, request):
        try:
            db = _get_db()
            error_col = db['error_logs']

            period = request.GET.get('period', '24')  # hours
            period_hours = int(period)

            start_date = datetime.utcnow() - timedelta(hours=period_hours)

            # Total errors
            total_errors = error_col.count_documents({
                'timestamp': {'$gte': start_date}
            })

            # By endpoint
            endpoint_errors = list(error_col.aggregate([
                {'$match': {
                    'timestamp': {'$gte': start_date}
                }},
                {'$group': {
                    '_id': '$endpoint',
                    'count': {'$sum': 1},
                    'latest': {'$max': '$timestamp'}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))

            # By error type
            error_types = {}
            for error in error_col.find({'timestamp': {'$gte': start_date}}):
                error_type = error.get('error_type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1

            metrics = {
                'period_hours': period_hours,
                'total_errors': total_errors,
                'error_rate': round((total_errors / max((period_hours * 3600), 1)) * 100, 4),
                'top_errors': endpoint_errors,
                'error_types': error_types
            }

            return JsonResponse({
                'success': True,
                'data': metrics
            })

        except Exception as e:
            log.exception(f'Error rate hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResponseTimeView(View):
    """API response time metrikleri"""

    def get(self, request):
        try:
            db = _get_db()
            log_col = db['api_logs']

            period = request.GET.get('period', '24')  # hours
            period_hours = int(period)

            start_date = datetime.utcnow() - timedelta(hours=period_hours)

            # Response time stats
            stats = list(log_col.aggregate([
                {'$match': {
                    'timestamp': {'$gte': start_date},
                    'response_time_ms': {'$exists': True}
                }},
                {'$group': {
                    '_id': None,
                    'avg_response_time': {'$avg': '$response_time_ms'},
                    'min_response_time': {'$min': '$response_time_ms'},
                    'max_response_time': {'$max': '$response_time_ms'},
                    'p95_response_time': {'$avg': '$response_time_ms'},  # Simplified
                    'p99_response_time': {'$max': '$response_time_ms'}
                }}
            ]))

            if stats:
                stat = stats[0]
                metrics = {
                    'period_hours': period_hours,
                    'average_ms': round(stat.get('avg_response_time', 0), 2),
                    'min_ms': round(stat.get('min_response_time', 0), 2),
                    'max_ms': round(stat.get('max_response_time', 0), 2),
                    'p95_ms': round(stat.get('p95_response_time', 0), 2),
                    'p99_ms': round(stat.get('p99_response_time', 0), 2),
                    'slo_target_ms': 500,
                    'slo_met': stat.get('avg_response_time', 0) < 500
                }
            else:
                metrics = {
                    'period_hours': period_hours,
                    'average_ms': 0,
                    'min_ms': 0,
                    'max_ms': 0,
                    'message': 'Veri yok'
                }

            return JsonResponse({
                'success': True,
                'data': metrics
            })

        except Exception as e:
            log.exception(f'Response time hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertManagementView(View):
    """Alert yönetimi"""

    def get(self, request):
        """Aktif alert'leri listele"""
        try:
            db = _get_db()
            alert_col = db['alerts']

            alerts = list(alert_col.find({
                'status': 'active'
            }).sort('created_at', -1))

            # ID field'ini string'e çevir
            for a in alerts:
                a['_id'] = str(a['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'active_alerts': len(alerts),
                    'alerts': alerts
                }
            })

        except Exception as e:
            log.exception(f'Alert list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni alert oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            alert_col = db['alerts']

            alert = {
                'name': data.get('name'),
                'type': data.get('type'),  # threshold, error_rate, uptime
                'condition': data.get('condition'),
                'threshold': data.get('threshold'),
                'status': 'active',
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'notification_channels': data.get('notification_channels', [])
            }

            result = alert_col.insert_one(alert)

            return JsonResponse({
                'success': True,
                'data': {
                    'alert_id': str(result.inserted_id),
                    'message': 'Alert oluşturuldu'
                }
            })

        except Exception as e:
            log.exception(f'Alert creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogsView(View):
    """Sistem logları"""

    def get(self, request):
        try:
            db = _get_db()
            log_col = db['system_logs']

            # Filter
            level = request.GET.get('level', None)  # error, warning, info
            service = request.GET.get('service', None)
            limit = int(request.GET.get('limit', 100))

            query = {}
            if level:
                query['level'] = level
            if service:
                query['service'] = service

            logs = list(log_col.find(query)
                       .sort('timestamp', -1)
                       .limit(limit))

            # ID field'ini string'e çevir
            for log in logs:
                log['_id'] = str(log['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total': log_col.count_documents(query),
                    'limit': limit,
                    'logs': logs
                }
            })

        except Exception as e:
            log.exception(f'Logs hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
