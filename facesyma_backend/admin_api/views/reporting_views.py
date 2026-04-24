"""
admin_api/views/reporting_views.py
==================================
Report Generation & Scheduling
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
import uuid

log = logging.getLogger(__name__)

_VALID_REPORT_TYPES = frozenset({'user_analysis', 'revenue', 'community', 'moderation', 'engagement', 'retention', 'custom'})
_REPORT_STAT_TYPES  = ['analytics', 'revenue', 'users', 'engagement']


@method_decorator(csrf_exempt, name='dispatch')
class ReportGeneratorView(View):
    """Custom rapor oluşturma"""

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
            _now = datetime.utcnow()
            db = _get_db()
            report_col = db['generated_reports']

            report = {
                'report_id': str(uuid.uuid4()),
                'report_type': str(_dget('report_type', ''))[:50],
                'title': str(_dget('title', ''))[:200],
                'description': str(_dget('description', ''))[:500],
                'period': str(_dget('period', ''))[:20],
                'start_date': _dget('start_date'),
                'end_date': _dget('end_date'),
                'metrics': _dget('metrics', []),
                'format': str(_dget('format', 'pdf'))[:20],
                'status': 'generating',
                'created_at': _now,
                'created_by': admin_payload.get('email', 'admin'),
                'completed_at': None,
                'file_size_kb': 0,
                'file_url': None
            }

            result = report_col.insert_one(report)
            _rid = report['report_id']
            log.info(f"Report generation started: {_rid}")

            report_col.update_one(
                {'_id': result.inserted_id},
                {'$set': {
                    'status': 'completed',
                    'completed_at': _now,
                    'file_size_kb': 1024,
                    'file_url': f'/reports/{_rid}.pdf'
                }}
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'report_id': _rid,
                    'status': 'completed',
                    'file_url': f'/reports/{_rid}.pdf'
                }
            })

        except Exception as e:
            log.exception(f'Report generation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportScheduleView(View):
    """Yapılandırılmış rapor zamanlaması"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            schedule_col = db['scheduled_reports']

            schedules = list(schedule_col.find({}, {'_id': 0}).sort('created_at', -1).limit(500))

            return JsonResponse({
                'success': True,
                'data': {
                    'total_schedules': len(schedules),
                    'active_schedules': sum(1 for s in schedules if s.get('enabled', True)),
                    'schedules': schedules
                }
            })

        except Exception as e:
            log.exception(f'Schedule list error: {e}')
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
            _now = datetime.utcnow()
            db = _get_db()
            schedule_col = db['scheduled_reports']

            schedule = {
                'schedule_id': str(uuid.uuid4()),
                'report_type': str(_dget('report_type', ''))[:50],
                'title': str(_dget('title', ''))[:200],
                'frequency': str(_dget('frequency', ''))[:20],
                'day_of_week': str(_dget('day_of_week', ''))[:20],
                'time_of_day': str(_dget('time_of_day', '09:00'))[:10],
                'recipients': _dget('recipients', []),
                'metrics': _dget('metrics', []),
                'format': str(_dget('format', 'pdf'))[:20],
                'enabled': bool(_dget('enabled', True)),
                'created_at': _now,
                'last_generated_at': None,
                'next_generation_at': None,
                'created_by': admin_payload.get('email', 'admin')
            }

            schedule_col.insert_one(schedule)
            _srtype = schedule['report_type']; _sfreq = schedule['frequency']
            log.info(f"Report schedule created: {_srtype} - {_sfreq}")

            return JsonResponse({
                'success': True,
                'data': {
                    'schedule_id': schedule['schedule_id'],
                    'report_type': _srtype,
                    'frequency': _sfreq
                }
            })

        except Exception as e:
            log.exception(f'Schedule creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportHistoryView(View):
    """Üretilmiş raporlar - arşiv"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            report_col = db['generated_reports']

            _qp = request.GET
            _qpget = _qp.get
            report_type = _qpget('type')

            try:
                days = min(max(1, int(_qpget('days', 90))), 365)
                limit = min(max(1, int(_qpget('limit', 50))), 200)
            except (ValueError, TypeError):
                days = 90
                limit = 50

            start_date = datetime.utcnow() - timedelta(days=days)
            query = {'created_at': {'$gte': start_date}}
            if report_type and report_type in _VALID_REPORT_TYPES:
                query['report_type'] = report_type

            reports = list(report_col.find(query).sort('created_at', -1).limit(limit))
            for r in reports:
                _oid = r['_id']
                r['_id'] = str(_oid)
                _cat = r.get('created_at')
                if isinstance(_cat, datetime):
                    r['created_at'] = _cat.isoformat()


            _rf = next(report_col.aggregate([{'$facet': {
                'total':    [{'$match': query}, {'$count': 'n'}],
                'by_type':  [
                    {'$match': {'report_type': {'$in': _REPORT_STAT_TYPES}, 'created_at': {'$gte': start_date}}},
                    {'$group': {'_id': '$report_type', 'count': {'$sum': 1}}},
                ],
            }}]), {})
            _rfget = _rf.get
            total_reports = (_rfget('total', [{}])[0] or {}).get('n', 0)
            stats = {rtype: 0 for rtype in _REPORT_STAT_TYPES}
            for doc in _rfget('by_type', []):
                _did = doc['_id']
                if _did in stats:
                    stats[_did] = doc['count']

            total_size = sum(r.get('file_size_kb', 0) for r in reports)

            return JsonResponse({
                'success': True,
                'data': {
                    'total_reports': total_reports,
                    'reports_by_type': stats,
                    'total_storage_kb': total_size,
                    'recent_reports': reports
                }
            })

        except Exception as e:
            log.exception(f'Report history error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
