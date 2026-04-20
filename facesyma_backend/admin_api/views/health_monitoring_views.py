"""
admin_api/views/health_monitoring_views.py
==========================================
Advanced Health Monitoring & Alert Management

Features:
  - Deep service health monitoring
  - Configurable alert rules
  - Alert history and escalation
  - SLA tracking
"""

import json
import logging
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
class HealthMonitoringView(View):
    """Detaylı sağlık izleme"""

    def get(self, request):
        """Gerçek zamanlı servis durumu"""
        try:
            db = _get_db()
            health_col = db['service_health']
            metrics_col = db['service_metrics']

            # Servis sağlığı kontrolleri
            services = ['django', 'fastapi-chat', 'coach-service', 'mongodb']
            service_status = {}

            now = datetime.utcnow()
            check_window = now - timedelta(minutes=5)

            for service in services:
                checks = list(health_col.find({
                    'service': service,
                    'timestamp': {'$gte': check_window}
                }).sort('timestamp', -1).limit(1))

                if checks:
                    check = checks[0]
                    service_status[service] = {
                        'status': check.get('status', 'unknown'),
                        'response_time_ms': check.get('response_time_ms', 0),
                        'last_check': check.get('timestamp', now).isoformat(),
                        'uptime_percentage': check.get('uptime_percentage', 100)
                    }
                else:
                    service_status[service] = {
                        'status': 'unknown',
                        'response_time_ms': 0,
                        'last_check': 'never',
                        'uptime_percentage': 0
                    }

            # Metrikler
            metrics = {}
            for service in services:
                latest_metric = metrics_col.find_one(
                    {'service': service},
                    sort=[('timestamp', -1)]
                )
                if latest_metric:
                    metrics[service] = {
                        'cpu_usage': latest_metric.get('cpu_usage', 0),
                        'memory_usage': latest_metric.get('memory_usage', 0),
                        'disk_usage': latest_metric.get('disk_usage', 0),
                        'connections': latest_metric.get('connections', 0)
                    }

            # Genel durum
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
            log.exception(f'Health monitoring hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertConfigView(View):
    """Alert kuralları - yapılandırma"""

    def get(self, request):
        """Alert kurallarını getir"""
        try:
            db = _get_db()
            alert_col = db['alert_rules']

            rules = list(alert_col.find())
            for r in rules:
                r['_id'] = str(r['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total_rules': len(rules),
                    'active_rules': sum(1 for r in rules if r.get('enabled', True)),
                    'rules': rules
                }
            })

        except Exception as e:
            log.exception(f'Alert config get hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Alert kuralı oluştur/güncelle"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            alert_col = db['alert_rules']

            rule = {
                'name': data.get('name'),
                'condition': data.get('condition'),  # uptime < 99%, error_rate > 1%, response_time > 500ms
                'threshold': data.get('threshold'),
                'metric': data.get('metric'),  # uptime, error_rate, response_time, cpu, memory
                'enabled': data.get('enabled', True),
                'severity': data.get('severity', 'medium'),  # low, medium, high, critical
                'notification_channels': data.get('notification_channels', ['email', 'slack']),
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system'
            }

            result = alert_col.insert_one(rule)

            log.info(f"Alert rule created: {rule['name']}")

            return JsonResponse({
                'success': True,
                'data': {
                    'rule_id': str(result.inserted_id),
                    'name': rule['name'],
                    'severity': rule['severity']
                }
            })

        except Exception as e:
            log.exception(f'Alert rule creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlertHistoryView(View):
    """Alert geçmişi ve istatistikleri"""

    def get(self, request):
        """Tetiklenen alert'leri getir"""
        try:
            db = _get_db()
            history_col = db['alert_history']

            days = int(request.GET.get('days', '30'))
            severity = request.GET.get('severity')
            limit = int(request.GET.get('limit', '100'))

            start_date = datetime.utcnow() - timedelta(days=days)

            query = {'timestamp': {'$gte': start_date}}
            if severity:
                query['severity'] = severity

            alerts = list(history_col.find(query)
                         .sort('timestamp', -1)
                         .limit(limit))

            for a in alerts:
                a['_id'] = str(a['_id'])
                if isinstance(a.get('timestamp'), datetime):
                    a['timestamp'] = a['timestamp'].isoformat()

            # Istatistik
            stats = {}
            for sev in ['low', 'medium', 'high', 'critical']:
                stats[sev] = history_col.count_documents({
                    'severity': sev,
                    'timestamp': {'$gte': start_date}
                })

            # Çözülme zamanı
            avg_resolution_time = 0
            resolved = list(history_col.aggregate([
                {'$match': {
                    'resolved_at': {'$exists': True},
                    'timestamp': {'$gte': start_date}
                }},
                {'$project': {
                    'resolution_time': {
                        '$subtract': ['$resolved_at', '$timestamp']
                    }
                }},
                {'$group': {
                    '_id': None,
                    'avg': {'$avg': '$resolution_time'}
                }}
            ]))

            if resolved:
                avg_resolution_time = resolved[0]['avg'] / 3600  # Saat cinsine çevir

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': days,
                    'total_alerts': history_col.count_documents(query),
                    'severity_breakdown': stats,
                    'avg_resolution_time_hours': round(avg_resolution_time, 2),
                    'recent_alerts': alerts
                }
            })

        except Exception as e:
            log.exception(f'Alert history hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
