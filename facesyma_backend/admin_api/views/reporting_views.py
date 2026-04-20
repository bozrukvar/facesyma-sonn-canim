"""
admin_api/views/reporting_views.py
==================================
Report Generation & Scheduling

Features:
  - Custom report generation
  - Scheduled recurring reports
  - Report templates
  - Export and archival
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
import uuid

log = logging.getLogger(__name__)


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class ReportGeneratorView(View):
    """Custom rapor oluşturma"""

    def post(self, request):
        """Yeni rapor oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            report_col = db['generated_reports']

            report = {
                'report_id': str(uuid.uuid4()),
                'report_type': data.get('report_type'),  # analytics, revenue, users, engagement
                'title': data.get('title'),
                'description': data.get('description'),
                'period': data.get('period'),  # daily, weekly, monthly
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'metrics': data.get('metrics', []),
                'format': data.get('format', 'pdf'),  # pdf, excel, html
                'status': 'generating',
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'completed_at': None,
                'file_size_kb': 0,
                'file_url': None
            }

            result = report_col.insert_one(report)

            log.info(f"Report generation started: {report['report_id']}")

            # Simülasyon: rapor oluşturma tamamlandı
            report_col.update_one(
                {'_id': result.inserted_id},
                {'$set': {
                    'status': 'completed',
                    'completed_at': datetime.utcnow(),
                    'file_size_kb': 1024,
                    'file_url': f'/reports/{report["report_id"]}.pdf'
                }}
            )

            return JsonResponse({
                'success': True,
                'data': {
                    'report_id': report['report_id'],
                    'status': 'completed',
                    'file_url': f'/reports/{report["report_id"]}.pdf'
                }
            })

        except Exception as e:
            log.exception(f'Report generation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportScheduleView(View):
    """Yapılandırılmış rapor zamanlaması"""

    def get(self, request):
        """Zamanlanmış raporları getir"""
        try:
            db = _get_db()
            schedule_col = db['scheduled_reports']

            schedules = list(schedule_col.find().sort('created_at', -1))

            for s in schedules:
                s['_id'] = str(s['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total_schedules': len(schedules),
                    'active_schedules': sum(1 for s in schedules if s.get('enabled', True)),
                    'schedules': schedules
                }
            })

        except Exception as e:
            log.exception(f'Schedule list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni zamanlanmış rapor oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            schedule_col = db['scheduled_reports']

            schedule = {
                'schedule_id': str(uuid.uuid4()),
                'report_type': data.get('report_type'),
                'title': data.get('title'),
                'frequency': data.get('frequency'),  # daily, weekly, monthly
                'day_of_week': data.get('day_of_week'),  # Monday, Tuesday...
                'time_of_day': data.get('time_of_day', '09:00'),
                'recipients': data.get('recipients', []),
                'metrics': data.get('metrics', []),
                'format': data.get('format', 'pdf'),
                'enabled': data.get('enabled', True),
                'created_at': datetime.utcnow(),
                'last_generated_at': None,
                'next_generation_at': None,
                'created_by': request.user.id if hasattr(request, 'user') else 'system'
            }

            result = schedule_col.insert_one(schedule)

            log.info(f"Report schedule created: {schedule['report_type']} - {schedule['frequency']}")

            return JsonResponse({
                'success': True,
                'data': {
                    'schedule_id': schedule['schedule_id'],
                    'report_type': schedule['report_type'],
                    'frequency': schedule['frequency']
                }
            })

        except Exception as e:
            log.exception(f'Schedule creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportHistoryView(View):
    """Üretilmiş raporlar - arşiv ve indirme"""

    def get(self, request):
        """Üretilmiş raporları listele"""
        try:
            db = _get_db()
            report_col = db['generated_reports']

            report_type = request.GET.get('type')
            days = int(request.GET.get('days', '90'))
            limit = int(request.GET.get('limit', '50'))

            start_date = datetime.utcnow() - timedelta(days=days)

            query = {'created_at': {'$gte': start_date}}
            if report_type:
                query['report_type'] = report_type

            reports = list(report_col.find(query)
                          .sort('created_at', -1)
                          .limit(limit))

            for r in reports:
                r['_id'] = str(r['_id'])
                if isinstance(r.get('created_at'), datetime):
                    r['created_at'] = r['created_at'].isoformat()

            # İstatistik
            stats = {}
            for rtype in ['analytics', 'revenue', 'users', 'engagement']:
                stats[rtype] = report_col.count_documents({
                    'report_type': rtype,
                    'created_at': {'$gte': start_date}
                })

            # Toplam boyut
            total_size = sum(r.get('file_size_kb', 0) for r in reports)

            return JsonResponse({
                'success': True,
                'data': {
                    'total_reports': report_col.count_documents(query),
                    'reports_by_type': stats,
                    'total_storage_kb': total_size,
                    'recent_reports': reports
                }
            })

        except Exception as e:
            log.exception(f'Report history hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
