"""
admin_api/views/content_views.py
================================
Content Management System

Features:
  - Dynamic coaching content management
  - Multi-language content sync
  - Publishing & scheduling
  - A/B testing setup
  - Content analytics
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

SUPPORTED_LANGUAGES = ['tr', 'en', 'de', 'ru', 'ar', 'es', 'ko', 'ja']


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class CoachingContentView(View):
    """Coaching içeriği yönetimi"""

    def get(self, request):
        """İçeriği listele"""
        try:
            db = _get_db()
            content_col = db['coaching_content']

            module = request.GET.get('module')  # kariyer, liderlik, daily
            lang = request.GET.get('lang', 'tr')
            status = request.GET.get('status')  # draft, published, scheduled
            limit = int(request.GET.get('limit', 50))

            query = {}
            if module:
                query['module'] = module
            if lang:
                query['languages'] = lang
            if status:
                query['status'] = status

            contents = list(content_col.find(query)
                           .sort('created_at', -1)
                           .limit(limit))

            for c in contents:
                c['_id'] = str(c['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total': content_col.count_documents(query),
                    'limit': limit,
                    'contents': contents
                }
            })

        except Exception as e:
            log.exception(f'Content list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni içerik oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            content_col = db['coaching_content']

            content = {
                'content_id': str(uuid.uuid4()),
                'module': data.get('module'),  # kariyer, liderlik, daily
                'title': data.get('title'),
                'description': data.get('description'),
                'body': data.get('body'),
                'languages': data.get('languages', ['tr']),
                'translations': data.get('translations', {}),  # {lang: {title, body}}
                'tags': data.get('tags', []),
                'status': 'draft',
                'visibility': data.get('visibility', 'public'),  # public, premium, members_only
                'publish_date': None,
                'schedule_date': None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'views': 0,
                'engagement_rate': 0
            }

            result = content_col.insert_one(content)

            log.info(f"Content created: {content['content_id']}")

            return JsonResponse({
                'success': True,
                'data': {
                    'content_id': content['content_id'],
                    'status': 'draft'
                }
            })

        except Exception as e:
            log.exception(f'Content creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentPublishView(View):
    """İçeriği yayınla veya zamanla"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            content_id = data.get('content_id')
            action = data.get('action')  # publish, schedule, unpublish

            db = _get_db()
            content_col = db['coaching_content']

            if action == 'publish':
                content_col.update_one(
                    {'content_id': content_id},
                    {'$set': {
                        'status': 'published',
                        'publish_date': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }}
                )
                log.info(f"Content published: {content_id}")

            elif action == 'schedule':
                schedule_date = data.get('schedule_date')
                content_col.update_one(
                    {'content_id': content_id},
                    {'$set': {
                        'status': 'scheduled',
                        'schedule_date': datetime.fromisoformat(schedule_date),
                        'updated_at': datetime.utcnow()
                    }}
                )
                log.info(f"Content scheduled: {content_id}")

            elif action == 'unpublish':
                content_col.update_one(
                    {'content_id': content_id},
                    {'$set': {
                        'status': 'draft',
                        'updated_at': datetime.utcnow()
                    }}
                )
                log.info(f"Content unpublished: {content_id}")

            return JsonResponse({
                'success': True,
                'data': {
                    'content_id': content_id,
                    'action': action
                }
            })

        except Exception as e:
            log.exception(f'Publish hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentTranslationView(View):
    """İçerik tercümesi & senkronizasyonu"""

    def post(self, request):
        """Dil tercümesi ekle"""
        try:
            data = json.loads(request.body)
            content_id = data.get('content_id')
            lang = data.get('language')
            translation = data.get('translation')  # {title, description, body}

            db = _get_db()
            content_col = db['coaching_content']

            # Add language to languages list if not exists
            content_col.update_one(
                {'content_id': content_id},
                {'$addToSet': {'languages': lang}}
            )

            # Add translation
            content_col.update_one(
                {'content_id': content_id},
                {'$set': {
                    f'translations.{lang}': translation,
                    'updated_at': datetime.utcnow()
                }}
            )

            log.info(f"Translation added: {content_id} -> {lang}")

            return JsonResponse({
                'success': True,
                'data': {
                    'content_id': content_id,
                    'language': lang,
                    'message': 'Translation added'
                }
            })

        except Exception as e:
            log.exception(f'Translation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ABTestingView(View):
    """A/B test yönetimi"""

    def get(self, request):
        """A/B testleri listele"""
        try:
            db = _get_db()
            test_col = db['ab_tests']

            status = request.GET.get('status')  # active, completed, archived

            query = {}
            if status:
                query['status'] = status

            tests = list(test_col.find(query)
                        .sort('created_at', -1)
                        .limit(50))

            for t in tests:
                t['_id'] = str(t['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'tests': tests
                }
            })

        except Exception as e:
            log.exception(f'Tests list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni A/B test oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            test_col = db['ab_tests']

            test = {
                'test_id': str(uuid.uuid4()),
                'name': data.get('name'),
                'content_id': data.get('content_id'),
                'variant_a': data.get('variant_a'),  # {title, body}
                'variant_b': data.get('variant_b'),  # {title, body}
                'status': 'active',
                'sample_size': data.get('sample_size', 1000),
                'duration_days': data.get('duration_days', 7),
                'metric': data.get('metric', 'engagement_rate'),  # engagement_rate, ctr
                'created_at': datetime.utcnow(),
                'end_date': datetime.utcnow() + timedelta(days=data.get('duration_days', 7)),
                'variant_a_results': {'views': 0, 'engagements': 0},
                'variant_b_results': {'views': 0, 'engagements': 0},
                'winner': None
            }

            result = test_col.insert_one(test)

            log.info(f"A/B test created: {test['test_id']}")

            return JsonResponse({
                'success': True,
                'data': {
                    'test_id': test['test_id'],
                    'status': 'active'
                }
            })

        except Exception as e:
            log.exception(f'Test creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentAnalyticsView(View):
    """İçerik analytics'i"""

    def get(self, request):
        try:
            db = _get_db()
            content_col = db['coaching_content']

            content_id = request.GET.get('content_id')
            module = request.GET.get('module')

            query = {}
            if content_id:
                query['content_id'] = content_id
            if module:
                query['module'] = module

            # Get analytics
            contents = list(content_col.find(query, {
                'content_id': 1,
                'title': 1,
                'module': 1,
                'views': 1,
                'engagement_rate': 1,
                'created_at': 1
            }).sort('views', -1).limit(20))

            # Calculate totals
            total_views = sum(c.get('views', 0) for c in contents)
            avg_engagement = sum(c.get('engagement_rate', 0) for c in contents) / max(len(contents), 1)

            analytics = {
                'contents_analyzed': len(contents),
                'total_views': total_views,
                'avg_engagement_rate': round(avg_engagement, 2),
                'top_contents': contents
            }

            return JsonResponse({
                'success': True,
                'data': analytics
            })

        except Exception as e:
            log.exception(f'Analytics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentTemplateView(View):
    """İçerik şablonları"""

    def get(self, request):
        """Şablonları listele"""
        try:
            db = _get_db()
            template_col = db['content_templates']

            templates = list(template_col.find().sort('created_at', -1))

            for t in templates:
                t['_id'] = str(t['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'templates': templates
                }
            })

        except Exception as e:
            log.exception(f'Templates list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni şablon oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            template_col = db['content_templates']

            template = {
                'template_id': str(uuid.uuid4()),
                'name': data.get('name'),
                'module': data.get('module'),
                'description': data.get('description'),
                'structure': data.get('structure'),  # JSON schema
                'fields': data.get('fields'),  # List of field definitions
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'usage_count': 0
            }

            result = template_col.insert_one(template)

            return JsonResponse({
                'success': True,
                'data': {
                    'template_id': template['template_id']
                }
            })

        except Exception as e:
            log.exception(f'Template creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
