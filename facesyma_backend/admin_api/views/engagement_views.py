"""
admin_api/views/engagement_views.py
===================================
User Engagement & Retention Tools
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

_VALID_CAMPAIGN_STATUSES = frozenset({'pending', 'sent', 'scheduled', 'draft', 'canceled', 'failed'})


@method_decorator(csrf_exempt, name='dispatch')
class PushNotificationCampaignView(View):
    """Push notification kampanyaları"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            campaign_col = db['push_campaigns']

            _qget = request.GET.get
            status = _qget('status')
            try:
                limit = min(max(1, int(_qget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50


            query = {}
            if status and status in _VALID_CAMPAIGN_STATUSES:
                query['status'] = status

            campaigns = list(campaign_col.find(query).sort('created_at', -1).limit(limit))
            for c in campaigns:
                _oid = c['_id']
                c['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {'total': campaign_col.count_documents(query), 'campaigns': campaigns}
            })

        except Exception as e:
            log.exception(f'Campaign list error: {e}')
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
            campaign_col = db['push_campaigns']

            campaign = {
                'campaign_id': str(uuid.uuid4()),
                'name': str(_dget('name', ''))[:100],
                'title': str(_dget('title', ''))[:200],
                'body': str(_dget('body', ''))[:1000],
                'target_segment': str(_dget('target_segment', ''))[:50],
                'target_count': 0,
                'status': 'draft',
                'schedule_type': str(_dget('schedule_type', ''))[:50],
                'schedule_date': _dget('schedule_date'),
                'schedule_time': _dget('schedule_time'),
                'created_at': datetime.utcnow(),
                'created_by': admin_payload.get('email', 'admin'),
                'sent_at': None,
                'stats': {'sent': 0, 'opened': 0, 'clicked': 0, 'dismissed': 0, 'conversion_count': 0}
            }

            campaign_col.insert_one(campaign)
            _cpid = campaign['campaign_id']
            log.info(f"Campaign created: {_cpid}")

            return JsonResponse({
                'success': True,
                'data': {'campaign_id': _cpid, 'status': 'draft'}
            })

        except Exception as e:
            log.exception(f'Campaign creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationTemplateView(View):
    """Notification şablonları"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            template_col = db['notification_templates']

            category = request.GET.get('category')
            query = {}
            if category:
                query['category'] = category

            templates = list(template_col.find(query, {'_id': 0}).sort('created_at', -1).limit(200))

            return JsonResponse({'success': True, 'data': {'templates': templates}})

        except Exception as e:
            log.exception(f'Template list error: {e}')
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
            template_col = db['notification_templates']

            template = {
                'template_id': str(uuid.uuid4()),
                'name': str(_dget('name', ''))[:100],
                'category': str(_dget('category', ''))[:50],
                'title': str(_dget('title', ''))[:200],
                'body': str(_dget('body', ''))[:1000],
                'action_url': str(_dget('action_url', ''))[:512],
                'image_url': str(_dget('image_url', ''))[:512],
                'variables': _dget('variables', []),
                'created_at': datetime.utcnow(),
                'created_by': admin_payload.get('email', 'admin'),
                'usage_count': 0
            }

            template_col.insert_one(template)

            return JsonResponse({
                'success': True,
                'data': {'template_id': template['template_id']}
            })

        except Exception as e:
            log.exception(f'Template creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EmailCampaignView(View):
    """Email kampanyaları"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            email_col = db['email_campaigns']

            status = request.GET.get('status')
            query = {}
            if status:
                query['status'] = status

            campaigns = list(email_col.find(query).sort('created_at', -1).limit(50))
            for c in campaigns:
                _oid = c['_id']
                c['_id'] = str(_oid)

            return JsonResponse({'success': True, 'data': {'campaigns': campaigns}})

        except Exception as e:
            log.exception(f'Email campaign list error: {e}')
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
            email_col = db['email_campaigns']

            campaign = {
                'campaign_id': str(uuid.uuid4()),
                'name': str(_dget('name', ''))[:100],
                'subject': str(_dget('subject', ''))[:200],
                'body_html': str(_dget('body_html', ''))[:50000],
                'from_email': str(_dget('from_email', 'noreply@facesyma.com'))[:254],
                'target_list': str(_dget('target_list', ''))[:50],
                'target_count': 0,
                'status': 'draft',
                'schedule_date': _dget('schedule_date'),
                'created_at': datetime.utcnow(),
                'created_by': admin_payload.get('email', 'admin'),
                'sent_at': None,
                'stats': {'sent': 0, 'opened': 0, 'clicked': 0, 'unsubscribed': 0, 'bounced': 0}
            }

            email_col.insert_one(campaign)
            _ecpid = campaign['campaign_id']
            log.info(f"Email campaign created: {_ecpid}")

            return JsonResponse({
                'success': True,
                'data': {'campaign_id': _ecpid}
            })

        except Exception as e:
            log.exception(f'Email campaign creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CampaignAnalyticsView(View):
    """Kampanya analytics"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            _qget = request.GET.get
            campaign_type = _qget('type')
            campaign_id = _qget('campaign_id')

            campaign_col = db['push_campaigns'] if campaign_type == 'push' else db['email_campaigns']
            query = {}
            if campaign_id:
                query['campaign_id'] = campaign_id

            campaigns = list(campaign_col.find(query, {'_id': 0}).limit(500))

            if campaigns:
                total_sent = total_opened = 0
                for c in campaigns:
                    _cs = c.get('stats') or {}
                    total_sent   += _cs.get('sent',   0)
                    total_opened += _cs.get('opened', 0)
                open_rate = (total_opened / max(total_sent, 1)) * 100

                analytics = {
                    'campaign_type': campaign_type,
                    'total_campaigns': len(campaigns),
                    'total_sent': total_sent,
                    'total_opened': total_opened,
                    'open_rate': round(open_rate, 2),
                    'campaigns': campaigns
                }
            else:
                analytics = {'message': 'No campaigns found'}

            return JsonResponse({'success': True, 'data': analytics})

        except Exception as e:
            log.exception(f'Analytics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationStatsView(View):
    """Notification istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            campaign_col = db['push_campaigns']

            try:
                period_days = min(max(1, int(request.GET.get('period', 30))), 365)
            except (ValueError, TypeError):
                period_days = 30

            start_date = datetime.utcnow() - timedelta(days=period_days)

            agg = list(campaign_col.aggregate([
                {'$match': {'sent_at': {'$gte': start_date}}},
                {'$group': {
                    '_id': None,
                    'sent_campaigns': {'$sum': 1},
                    'total_sent': {'$sum': '$stats.sent'},
                    'total_opened': {'$sum': '$stats.opened'},
                    'total_clicked': {'$sum': '$stats.clicked'},
                }}
            ]))
            row = agg[0] if agg else {}
            _rowget = row.get
            sent_campaigns = _rowget('sent_campaigns', 0)
            total_sent = _rowget('total_sent', 0)
            total_opened = _rowget('total_opened', 0)
            total_clicked = _rowget('total_clicked', 0)

            open_rate = (total_opened / max(total_sent, 1)) * 100
            ctr = (total_clicked / max(total_opened, 1)) * 100

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': period_days,
                    'sent_campaigns': sent_campaigns,
                    'total_sent': total_sent,
                    'total_opened': total_opened,
                    'total_clicked': total_clicked,
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(ctr, 2)
                }
            })

        except Exception as e:
            log.exception(f'Notification stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
