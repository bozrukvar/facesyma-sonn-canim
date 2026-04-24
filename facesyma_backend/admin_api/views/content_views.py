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
import re
from datetime import datetime, timedelta

_RE_MODULE = re.compile(r'^[a-zA-Z0-9_]{1,50}$')
_RE_LANG   = re.compile(r'^[a-z]{2,5}$')
_RE_UUID   = re.compile(r'^[a-f0-9\-]{1,36}$')
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin
import uuid

log = logging.getLogger(__name__)

SUPPORTED_LANGUAGES  = ['tr', 'en', 'de', 'ru', 'ar', 'es', 'ko', 'ja']
_CONTENT_STATS_PROJ  = {'content_id': 1, 'title': 1, 'module': 1, 'views': 1, 'engagement_rate': 1, 'created_at': 1}

_VALID_CONTENT_STATUSES = frozenset({'draft', 'published', 'archived'})
_VALID_CONTENT_ACTIONS  = frozenset({'publish', 'schedule', 'unpublish'})
_VALID_AB_STATUSES      = frozenset({'draft', 'active', 'paused', 'completed', 'archived'})


@method_decorator(csrf_exempt, name='dispatch')
class CoachingContentView(View):
    """Coaching içeriği yönetimi"""

    def get(self, request):
        """İçeriği listele"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            content_col = db['coaching_content']

            _qp = request.GET
            _qpget = _qp.get
            module = _qpget('module')
            lang = _qpget('lang', 'tr')
            status = _qpget('status')
            try:
                limit = min(max(1, int(_qpget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50


            query = {}
            if module and _RE_MODULE.match(module):
                query['module'] = module
            if lang and _RE_LANG.match(lang):
                query['languages'] = lang
            if status and status in _VALID_CONTENT_STATUSES:
                query['status'] = status

            contents = list(content_col.find(query).sort('created_at', -1).limit(limit))
            for c in contents:
                _oid = c['_id']
                c['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {
                    'total': content_col.count_documents(query),
                    'limit': limit,
                    'contents': contents
                }
            })

        except Exception as e:
            log.exception(f'Content list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        """Yeni içerik oluştur"""
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
            content_col = db['coaching_content']

            content = {
                'content_id': str(uuid.uuid4()),
                'module': str(_dget('module', ''))[:50],
                'title': str(_dget('title', ''))[:200],
                'description': str(_dget('description', ''))[:500],
                'body': str(_dget('body', ''))[:10000],
                'languages': [l for l in _dget('languages', ['tr']) if isinstance(l, str) and _RE_LANG.match(l)][:20],
                'translations': _dget('translations', {}),
                'tags': [str(t)[:50] for t in _dget('tags', []) if isinstance(t, str)][:20],
                'status': 'draft',
                'visibility': str(_dget('visibility', 'public'))[:20],
                'publish_date': None,
                'schedule_date': None,
                'created_at': _now,
                'updated_at': _now,
                'created_by': admin_payload.get('email', 'admin'),
                'views': 0,
                'engagement_rate': 0
            }

            content_col.insert_one(content)
            _ccid = content['content_id']
            log.info(f"Content created: {_ccid}")

            return JsonResponse({
                'success': True,
                'data': {'content_id': _ccid, 'status': 'draft'}
            })

        except Exception as e:
            log.exception(f'Content creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentPublishView(View):
    """İçeriği yayınla veya zamanla"""

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
            content_id = _dget('content_id')
            action = _dget('action')

            if action not in _VALID_CONTENT_ACTIONS:
                return JsonResponse({'detail': f'Invalid action. Allowed: {", ".join(sorted(_VALID_CONTENT_ACTIONS))}'}, status=400)
            if not content_id:
                return JsonResponse({'detail': 'content_id is required'}, status=400)

            _now = datetime.utcnow()
            db = _get_db()
            content_col = db['coaching_content']
            _upd = content_col.update_one
            _li = log.info

            if action == 'publish':
                _upd(
                    {'content_id': content_id},
                    {'$set': {'status': 'published', 'publish_date': _now, 'updated_at': _now}}
                )
                _li(f"Content published: {content_id}")

            elif action == 'schedule':
                schedule_date_str = _dget('schedule_date', '')
                try:
                    schedule_date = datetime.fromisoformat(schedule_date_str)
                except (ValueError, TypeError):
                    return JsonResponse({'detail': 'Invalid schedule_date format. Use ISO 8601.'}, status=400)
                _upd(
                    {'content_id': content_id},
                    {'$set': {'status': 'scheduled', 'schedule_date': schedule_date, 'updated_at': _now}}
                )
                _li(f"Content scheduled: {content_id}")

            elif action == 'unpublish':
                _upd(
                    {'content_id': content_id},
                    {'$set': {'status': 'draft', 'updated_at': _now}}
                )
                _li(f"Content unpublished: {content_id}")

            return JsonResponse({
                'success': True,
                'data': {'content_id': content_id, 'action': action}
            })

        except Exception as e:
            log.exception(f'Publish error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentTranslationView(View):
    """İçerik tercümesi & senkronizasyonu"""

    def post(self, request):
        """Dil tercümesi ekle"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            content_id = _dget('content_id')
            lang = str(_dget('language', ''))[:10]
            translation = _dget('translation')

            if not content_id or not lang:
                return JsonResponse({'detail': 'content_id and language are required'}, status=400)
            if lang not in SUPPORTED_LANGUAGES:
                return JsonResponse({'detail': f'Unsupported language. Allowed: {", ".join(SUPPORTED_LANGUAGES)}'}, status=400)

            _now = datetime.utcnow()
            db = _get_db()
            content_col = db['coaching_content']
            _ccuo = content_col.update_one

            _ccuo(
                {'content_id': content_id},
                {'$addToSet': {'languages': lang}}
            )
            _ccuo(
                {'content_id': content_id},
                {'$set': {f'translations.{lang}': translation, 'updated_at': _now}}
            )

            log.info(f"Translation added: {content_id} -> {lang}")

            return JsonResponse({
                'success': True,
                'data': {'content_id': content_id, 'language': lang, 'message': 'Translation added'}
            })

        except Exception as e:
            log.exception(f'Translation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ABTestingView(View):
    """A/B test yönetimi"""

    def get(self, request):
        """A/B testleri listele"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            test_col = db['ab_tests']


            _qp = request.GET
            _qpget = _qp.get
            status = _qpget('status')
            query = {}
            if status and status in _VALID_AB_STATUSES:
                query['status'] = status

            tests = list(test_col.find(query).sort('created_at', -1).limit(50))
            for t in tests:
                _oid = t['_id']
                t['_id'] = str(_oid)

            return JsonResponse({'success': True, 'data': {'tests': tests}})

        except Exception as e:
            log.exception(f'Tests list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        """Yeni A/B test oluştur"""
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
            test_col = db['ab_tests']

            try:
                duration_days = max(1, int(_dget('duration_days', 7)))
                sample_size = max(1, int(_dget('sample_size', 1000)))
            except (TypeError, ValueError):
                duration_days = 7
                sample_size = 1000

            test = {
                'test_id': str(uuid.uuid4()),
                'name': str(_dget('name', ''))[:100],
                'content_id': _dget('content_id'),
                'variant_a': _dget('variant_a'),
                'variant_b': _dget('variant_b'),
                'status': 'active',
                'sample_size': sample_size,
                'duration_days': duration_days,
                'metric': str(_dget('metric', 'engagement_rate'))[:50],
                'created_at': _now,
                'end_date': _now + timedelta(days=duration_days),
                'variant_a_results': {'views': 0, 'engagements': 0},
                'variant_b_results': {'views': 0, 'engagements': 0},
                'created_by': admin_payload.get('email', 'admin'),
                'winner': None
            }

            test_col.insert_one(test)
            _ttid = test['test_id']
            log.info(f"A/B test created: {_ttid}")

            return JsonResponse({
                'success': True,
                'data': {'test_id': _ttid, 'status': 'active'}
            })

        except Exception as e:
            log.exception(f'Test creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentAnalyticsView(View):
    """İçerik analytics'i"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            content_col = db['coaching_content']

            _qp = request.GET
            _qpget = _qp.get
            content_id = _qpget('content_id', '')
            module = _qpget('module', '')

            query = {}
            if content_id and _RE_UUID.match(content_id):
                query['content_id'] = content_id
            if module and _RE_MODULE.match(module):
                query['module'] = module

            contents = list(content_col.find(query, _CONTENT_STATS_PROJ).sort('views', -1).limit(20))

            for c in contents:
                _oid = c['_id']
                c['_id'] = str(_oid)

            _n_contents = len(contents)
            total_views = total_eng = 0
            for c in contents:
                total_views += c.get('views', 0)
                total_eng   += c.get('engagement_rate', 0)
            avg_engagement = total_eng / max(_n_contents, 1)

            return JsonResponse({
                'success': True,
                'data': {
                    'contents_analyzed': _n_contents,
                    'total_views': total_views,
                    'avg_engagement_rate': round(avg_engagement, 2),
                    'top_contents': contents
                }
            })

        except Exception as e:
            log.exception(f'Analytics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentTemplateView(View):
    """İçerik şablonları"""

    def get(self, request):
        """Şablonları listele"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            template_col = db['content_templates']

            templates = list(template_col.find({}, {'_id': 0}).sort('created_at', -1).limit(100))

            return JsonResponse({'success': True, 'data': {'templates': templates}})

        except Exception as e:
            log.exception(f'Templates list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        """Yeni şablon oluştur"""
        try:
            admin_payload = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _now = datetime.utcnow()
            db = _get_db()
            template_col = db['content_templates']

            _dget = data.get
            template = {
                'template_id': str(uuid.uuid4()),
                'name': str(_dget('name', ''))[:100],
                'module': str(_dget('module', ''))[:50],
                'description': str(_dget('description', ''))[:500],
                'structure': _dget('structure'),
                'fields': _dget('fields'),
                'created_at': _now,
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
