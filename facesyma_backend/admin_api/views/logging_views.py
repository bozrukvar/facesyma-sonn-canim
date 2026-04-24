"""
admin_api/views/logging_views.py
================================
Log Aggregation & Analysis
"""

import json
import logging
import csv
from datetime import datetime, timedelta
from io import StringIO
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_VALID_LEVELS = {'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'}
_VALID_SERVICES = {'django', 'fastapi-chat', 'coach-service', 'face-validation', 'finetune', 'test-service'}


@method_decorator(csrf_exempt, name='dispatch')
class LogAggregationView(View):
    """Merkezi log toplama ve filtreleme"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            log_col = db['application_logs']

            _qp = request.GET
            _qpget = _qp.get
            level = _qpget('level')
            service = _qpget('service')
            try:
                days = min(max(1, int(_qpget('days', 7))), 90)
                limit = min(max(1, int(_qpget('limit', 100))), 500)
            except (ValueError, TypeError):
                days = 7
                limit = 100

            start_date = datetime.utcnow() - timedelta(days=days)
            query = {'timestamp': {'$gte': start_date}}
            if level and level in _VALID_LEVELS:
                query['level'] = level
            if service and service in _VALID_SERVICES:
                query['service'] = service

            logs = list(log_col.find(query).sort('timestamp', -1).limit(limit))
            for entry in logs:
                _oid = entry['_id']
                entry['_id'] = str(_oid)

            _ls = next(log_col.aggregate([{'$facet': {
                'total':    [{'$match': query}, {'$count': 'n'}],
                'INFO':     [{'$match': {'level': 'INFO',     'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
                'WARNING':  [{'$match': {'level': 'WARNING',  'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
                'ERROR':    [{'$match': {'level': 'ERROR',    'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
                'CRITICAL': [{'$match': {'level': 'CRITICAL', 'timestamp': {'$gte': start_date}}}, {'$count': 'n'}],
            }}]), {})
            stats = {lvl: (_ls.get(lvl, [{}])[0] or {}).get('n', 0) for lvl in ('INFO', 'WARNING', 'ERROR', 'CRITICAL')}
            total_logs = (_ls.get('total', [{}])[0] or {}).get('n', 0)

            return JsonResponse({
                'success': True,
                'data': {
                    'total_logs': total_logs,
                    'logs': logs,
                    'level_breakdown': stats,
                    'period_days': days
                }
            })

        except Exception as e:
            log.exception(f'Log aggregation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogAnalysisView(View):
    """Log analizi - pattern tespiti"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            log_col = db['application_logs']

            try:
                _qp = request.GET
                _qpget = _qp.get
                days = min(max(1, int(_qpget('days', 30))), 90)
            except (ValueError, TypeError):
                days = 30

            start_date = datetime.utcnow() - timedelta(days=days)

            _lr = next(log_col.aggregate([{'$match': {'timestamp': {'$gte': start_date}}}, {'$facet': {
                'top_errors': [
                    {'$match': {'level': 'ERROR'}},
                    {'$group': {'_id': '$message', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}}, {'$limit': 10},
                ],
                'error_trend': [
                    {'$match': {'level': 'ERROR'}},
                    {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}}, 'error_count': {'$sum': 1}}},
                    {'$sort': {'_id': 1}},
                ],
                'service_breakdown': [
                    {'$group': {'_id': '$service', 'count': {'$sum': 1}, 'errors': {'$sum': {'$cond': [{'$eq': ['$level', 'ERROR']}, 1, 0]}}}},
                ],
            }}]), {})
            _lrget = _lr.get
            top_errors        = _lrget('top_errors', [])
            error_trend       = _lrget('error_trend', [])
            service_breakdown = _lrget('service_breakdown', [])

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': days,
                    'top_errors': top_errors,
                    'error_trend': error_trend,
                    'service_breakdown': service_breakdown,
                    'total_errors': sum(e['count'] for e in top_errors),
                    'critical_issues': len([e for e in top_errors if e['count'] > 100])
                }
            })

        except Exception as e:
            log.exception(f'Log analysis error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LogExportView(View):
    """Log export - CSV/JSON"""

    def post(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            format_type = str(_dget('format', 'json'))
            if format_type not in ('json', 'csv'):
                format_type = 'json'
            try:
                days = min(max(1, int(_dget('days', 7))), 90)
            except (TypeError, ValueError):
                days = 7
            level = _dget('level')

            _now = datetime.utcnow()
            db = _get_db()
            log_col = db['application_logs']

            start_date = _now - timedelta(days=days)
            query = {'timestamp': {'$gte': start_date}}
            if level and level in _VALID_LEVELS:
                query['level'] = level

            logs = list(log_col.find(query).sort('timestamp', -1).limit(10000))
            _now_fmt = _now_fmt

            if format_type == 'csv':
                output = StringIO()
                if logs:
                    writer = csv.DictWriter(output, fieldnames=['timestamp', 'level', 'service', 'message'])
                    writer.writeheader()
                    for log_entry in logs:
                        _leget = log_entry.get
                        writer.writerow({
                            'timestamp': _leget('timestamp', ''),
                            'level': _leget('level', ''),
                            'service': _leget('service', ''),
                            'message': _leget('message', '')
                        })

                return JsonResponse({
                    'success': True,
                    'data': {
                        'format': 'csv',
                        'records': len(logs),
                        'content': output.getvalue(),
                        'filename': f'logs_{_now_fmt}.csv'
                    }
                })
            else:
                for entry in logs:
                    _oid = entry['_id']
                    entry['_id'] = str(_oid)
                    _ts = entry.get('timestamp')
                    if isinstance(_ts, datetime):
                        entry['timestamp'] = _ts.isoformat()

                return JsonResponse({
                    'success': True,
                    'data': {
                        'format': 'json',
                        'records': len(logs),
                        'logs': logs,
                        'filename': f'logs_{_now_fmt}.json'
                    }
                })

        except Exception as e:
            log.exception(f'Log export error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
