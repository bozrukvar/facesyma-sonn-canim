"""
admin_api/views/logging_views.py
================================
Log Aggregation & Analysis

Features:
  - Centralized log collection
  - Log analysis and pattern detection
  - Log export (CSV, JSON)
  - Error trend analysis
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
import csv
from io import StringIO

log = logging.getLogger(__name__)


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class LogAggregationView(View):
    """Merkezi log toplama ve filtreleme"""

    def get(self, request):
        """Toplanan logları getir"""
        try:
            db = _get_db()
            log_col = db['application_logs']

            # Filtreler
            level = request.GET.get('level')  # INFO, WARNING, ERROR, CRITICAL
            service = request.GET.get('service')  # django, fastapi, coach
            days = int(request.GET.get('days', '7'))
            limit = int(request.GET.get('limit', '100'))

            start_date = datetime.utcnow() - timedelta(days=days)

            query = {'timestamp': {'$gte': start_date}}
            if level:
                query['level'] = level
            if service:
                query['service'] = service

            logs = list(log_col.find(query)
                       .sort('timestamp', -1)
                       .limit(limit))

            for l in logs:
                l['_id'] = str(l['_id'])

            # İstatistik
            stats = {}
            for level_name in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                stats[level_name] = log_col.count_documents({
                    'level': level_name,
                    'timestamp': {'$gte': start_date}
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'total_logs': log_col.count_documents(query),
                    'logs': logs,
                    'level_breakdown': stats,
                    'period_days': days
                }
            })

        except Exception as e:
            log.exception(f'Log aggregation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogAnalysisView(View):
    """Log analizi - pattern tespiti"""

    def get(self, request):
        """Log desenlerini analiz et"""
        try:
            db = _get_db()
            log_col = db['application_logs']

            days = int(request.GET.get('days', '30'))
            start_date = datetime.utcnow() - timedelta(days=days)

            # En sık hatalar
            top_errors = list(log_col.aggregate([
                {'$match': {
                    'level': 'ERROR',
                    'timestamp': {'$gte': start_date}
                }},
                {'$group': {
                    '_id': '$message',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))

            # Hata oranı trendi
            error_trend = list(log_col.aggregate([
                {'$match': {
                    'level': 'ERROR',
                    'timestamp': {'$gte': start_date}
                }},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                    'error_count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]))

            # Service-wise breakdown
            service_breakdown = list(log_col.aggregate([
                {'$match': {'timestamp': {'$gte': start_date}}},
                {'$group': {
                    '_id': '$service',
                    'count': {'$sum': 1},
                    'errors': {
                        '$sum': {'$cond': [{'$eq': ['$level', 'ERROR']}, 1, 0]}
                    }
                }}
            ]))

            analysis = {
                'period_days': days,
                'top_errors': top_errors,
                'error_trend': error_trend,
                'service_breakdown': service_breakdown,
                'total_errors': sum(e['count'] for e in top_errors),
                'critical_issues': len([e for e in top_errors if e['count'] > 100])
            }

            return JsonResponse({
                'success': True,
                'data': analysis
            })

        except Exception as e:
            log.exception(f'Log analysis hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogExportView(View):
    """Log export - CSV/JSON"""

    def post(self, request):
        """Log'ları dış formatında export et"""
        try:
            data = json.loads(request.body)
            format_type = data.get('format', 'json')  # json, csv
            days = data.get('days', 7)
            level = data.get('level')

            db = _get_db()
            log_col = db['application_logs']

            start_date = datetime.utcnow() - timedelta(days=days)
            query = {'timestamp': {'$gte': start_date}}
            if level:
                query['level'] = level

            logs = list(log_col.find(query).sort('timestamp', -1))

            if format_type == 'csv':
                # CSV formatı
                output = StringIO()
                if logs:
                    writer = csv.DictWriter(
                        output,
                        fieldnames=['timestamp', 'level', 'service', 'message']
                    )
                    writer.writeheader()

                    for log_entry in logs:
                        writer.writerow({
                            'timestamp': log_entry.get('timestamp', ''),
                            'level': log_entry.get('level', ''),
                            'service': log_entry.get('service', ''),
                            'message': log_entry.get('message', '')
                        })

                csv_data = output.getvalue()

                return JsonResponse({
                    'success': True,
                    'data': {
                        'format': 'csv',
                        'records': len(logs),
                        'content': csv_data,
                        'filename': f'logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
                    }
                })

            else:
                # JSON formatı
                for l in logs:
                    l['_id'] = str(l['_id'])
                    if isinstance(l.get('timestamp'), datetime):
                        l['timestamp'] = l['timestamp'].isoformat()

                return JsonResponse({
                    'success': True,
                    'data': {
                        'format': 'json',
                        'records': len(logs),
                        'logs': logs,
                        'filename': f'logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
                    }
                })

        except Exception as e:
            log.exception(f'Log export hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
