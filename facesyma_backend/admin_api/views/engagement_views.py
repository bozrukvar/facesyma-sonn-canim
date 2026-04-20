"""
admin_api/views/engagement_views.py
===================================
User Engagement & Retention Tools

Features:
  - Push notification dashboard
  - Email campaign management
  - Notification templates
  - Campaign analytics
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
class PushNotificationCampaignView(View):
    """Push notification kampanyaları"""

    def get(self, request):
        """Kampanyaları listele"""
        try:
            db = _get_db()
            campaign_col = db['push_campaigns']

            status = request.GET.get('status')  # draft, scheduled, sent, paused
            limit = int(request.GET.get('limit', 50))

            query = {}
            if status:
                query['status'] = status

            campaigns = list(campaign_col.find(query)
                            .sort('created_at', -1)
                            .limit(limit))

            for c in campaigns:
                c['_id'] = str(c['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total': campaign_col.count_documents(query),
                    'campaigns': campaigns
                }
            })

        except Exception as e:
            log.exception(f'Campaign list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni kampanya oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            campaign_col = db['push_campaigns']

            campaign = {
                'campaign_id': str(uuid.uuid4()),
                'name': data.get('name'),
                'title': data.get('title'),
                'body': data.get('body'),
                'target_segment': data.get('target_segment'),  # all, premium, ios, android
                'target_count': 0,
                'status': 'draft',
                'schedule_type': data.get('schedule_type'),  # immediate, scheduled, recurring
                'schedule_date': data.get('schedule_date'),
                'schedule_time': data.get('schedule_time'),
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'sent_at': None,
                'stats': {
                    'sent': 0,
                    'opened': 0,
                    'clicked': 0,
                    'dismissed': 0,
                    'conversion_count': 0
                }
            }

            result = campaign_col.insert_one(campaign)

            log.info(f"Campaign created: {campaign['campaign_id']}")

            return JsonResponse({
                'success': True,
                'data': {
                    'campaign_id': campaign['campaign_id'],
                    'status': 'draft'
                }
            })

        except Exception as e:
            log.exception(f'Campaign creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationTemplateView(View):
    """Notification şablonları"""

    def get(self, request):
        """Şablonları listele"""
        try:
            db = _get_db()
            template_col = db['notification_templates']

            category = request.GET.get('category')  # welcome, achievement, reminder, offer

            query = {}
            if category:
                query['category'] = category

            templates = list(template_col.find(query).sort('created_at', -1))

            for t in templates:
                t['_id'] = str(t['_id'])

            return JsonResponse({
                'success': True,
                'data': {'templates': templates}
            })

        except Exception as e:
            log.exception(f'Template list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni şablon oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            template_col = db['notification_templates']

            template = {
                'template_id': str(uuid.uuid4()),
                'name': data.get('name'),
                'category': data.get('category'),
                'title': data.get('title'),
                'body': data.get('body'),
                'action_url': data.get('action_url'),
                'image_url': data.get('image_url'),
                'variables': data.get('variables', []),
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'usage_count': 0
            }

            result = template_col.insert_one(template)

            return JsonResponse({
                'success': True,
                'data': {'template_id': template['template_id']}
            })

        except Exception as e:
            log.exception(f'Template creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EmailCampaignView(View):
    """Email kampanyaları"""

    def get(self, request):
        """Email kampanyalarını listele"""
        try:
            db = _get_db()
            email_col = db['email_campaigns']

            status = request.GET.get('status')

            query = {}
            if status:
                query['status'] = status

            campaigns = list(email_col.find(query)
                            .sort('created_at', -1)
                            .limit(50))

            for c in campaigns:
                c['_id'] = str(c['_id'])

            return JsonResponse({
                'success': True,
                'data': {'campaigns': campaigns}
            })

        except Exception as e:
            log.exception(f'Email campaign list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Email kampanyası oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            email_col = db['email_campaigns']

            campaign = {
                'campaign_id': str(uuid.uuid4()),
                'name': data.get('name'),
                'subject': data.get('subject'),
                'body_html': data.get('body_html'),
                'from_email': data.get('from_email', 'noreply@facesyma.com'),
                'target_list': data.get('target_list'),  # all, premium, inactive
                'target_count': 0,
                'status': 'draft',
                'schedule_date': data.get('schedule_date'),
                'created_at': datetime.utcnow(),
                'sent_at': None,
                'stats': {
                    'sent': 0,
                    'opened': 0,
                    'clicked': 0,
                    'unsubscribed': 0,
                    'bounced': 0
                }
            }

            result = email_col.insert_one(campaign)

            log.info(f"Email campaign created: {campaign['campaign_id']}")

            return JsonResponse({
                'success': True,
                'data': {'campaign_id': campaign['campaign_id']}
            })

        except Exception as e:
            log.exception(f'Email campaign creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CampaignAnalyticsView(View):
    """Kampanya analytics"""

    def get(self, request):
        try:
            db = _get_db()

            campaign_type = request.GET.get('type')  # push, email
            campaign_id = request.GET.get('campaign_id')

            if campaign_type == 'push':
                campaign_col = db['push_campaigns']
            else:
                campaign_col = db['email_campaigns']

            query = {}
            if campaign_id:
                query['campaign_id'] = campaign_id

            campaigns = list(campaign_col.find(query))

            # Aggregate stats
            if campaigns:
                total_sent = sum(c.get('stats', {}).get('sent', 0) for c in campaigns)
                total_opened = sum(c.get('stats', {}).get('opened', 0) for c in campaigns)

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

            return JsonResponse({
                'success': True,
                'data': analytics
            })

        except Exception as e:
            log.exception(f'Analytics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationStatsView(View):
    """Notification istatistikleri"""

    def get(self, request):
        try:
            db = _get_db()
            campaign_col = db['push_campaigns']

            period = request.GET.get('period', '30')
            period_days = int(period)

            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Sent campaigns
            sent_campaigns = campaign_col.count_documents({
                'sent_at': {'$gte': start_date}
            })

            # Total sent notifications
            campaigns = list(campaign_col.find({
                'sent_at': {'$gte': start_date}
            }))

            total_sent = sum(c.get('stats', {}).get('sent', 0) for c in campaigns)
            total_opened = sum(c.get('stats', {}).get('opened', 0) for c in campaigns)
            total_clicked = sum(c.get('stats', {}).get('clicked', 0) for c in campaigns)

            open_rate = (total_opened / max(total_sent, 1)) * 100
            ctr = (total_clicked / max(total_opened, 1)) * 100

            stats = {
                'period_days': period_days,
                'sent_campaigns': sent_campaigns,
                'total_sent': total_sent,
                'total_opened': total_opened,
                'total_clicked': total_clicked,
                'open_rate': round(open_rate, 2),
                'click_rate': round(ctr, 2)
            }

            return JsonResponse({
                'success': True,
                'data': stats
            })

        except Exception as e:
            log.exception(f'Notification stats hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
