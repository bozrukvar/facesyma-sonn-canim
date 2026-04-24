"""
admin_api/views/moderation_views.py
===================================
Content Moderation & Safety

Features:
  - User reports management
  - Content moderation (AI-powered)
  - Community guidelines enforcement
  - Ban/block management
  - Moderation logs
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from bson import ObjectId
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_VALID_REPORT_STATUSES    = frozenset({'pending', 'resolved', 'dismissed'})
_VALID_MOD_ACTIONS        = frozenset({'dismiss', 'warn', 'suspend', 'ban'})
_INAPPROPRIATE_KEYWORDS   = ['spam', 'abuse', 'hate', 'violence', 'porn']


@method_decorator(csrf_exempt, name='dispatch')
class UserReportsView(View):
    """Kullanıcı şikayet yönetimi"""

    def get(self, request):
        """Şikayetleri listele (admin only)"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            report_col = db['user_reports']

            _qget = request.GET.get
            status = _qget('status', None)
            try:
                limit = min(max(1, int(_qget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50


            query = {}
            if status and status in _VALID_REPORT_STATUSES:
                query['status'] = status

            reports = list(report_col.find(query).sort('created_at', -1).limit(limit))
            for r in reports:
                _oid = r['_id']
                r['_id'] = str(_oid)

            return JsonResponse({
                'success': True,
                'data': {
                    'total': report_col.count_documents(query),
                    'limit': limit,
                    'reports': reports
                }
            })

        except Exception as e:
            log.exception(f'Reports list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        """Yeni şikayet oluştur (admin only)"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            db = _get_db()
            report_col = db['user_reports']

            report = {
                'reporter_id': _dget('reporter_id'),
                'reported_user_id': _dget('reported_user_id'),
                'report_type': str(_dget('report_type', ''))[:50],
                'content_type': str(_dget('content_type', ''))[:50],
                'content_id': _dget('content_id'),
                'reason': str(_dget('reason', ''))[:200],
                'description': str(_dget('description', ''))[:1000],
                'status': 'pending',
                'severity': 'medium',
                'created_at': datetime.utcnow(),
                'reviewed_at': None,
                'reviewed_by': None,
                'action_taken': None
            }

            result = report_col.insert_one(report)
            _rid = result.inserted_id
            log.info(f"User report created: {_rid}")

            return JsonResponse({
                'success': True,
                'data': {'report_id': str(_rid), 'status': 'pending'}
            })

        except Exception as e:
            log.exception(f'Report creation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportReviewView(View):
    """Şikayet gözden geçirme ve işlem"""

    def post(self, request):
        """Şikayeti gözden geçir ve karar ver"""
        try:
            admin_payload = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            report_id_raw = _dget('report_id')
            action = _dget('action')

            if action not in _VALID_MOD_ACTIONS:
                return JsonResponse({'detail': f'Invalid action. Allowed: {", ".join(sorted(_VALID_MOD_ACTIONS))}'}, status=400)
            notes = str(_dget('notes', ''))[:500]

            try:
                report_id = ObjectId(report_id_raw)
            except Exception:
                return JsonResponse({'detail': 'Invalid report_id format.'}, status=400)

            _now = datetime.utcnow()
            db = _get_db()
            report_col = db['user_reports']
            user_col = db['appfaceapi_myuser']
            action_col = db['moderation_actions']

            admin_email = admin_payload.get('email', 'admin')

            report_col.update_one(
                {'_id': report_id},
                {'$set': {
                    'status': 'resolved' if action != 'dismiss' else 'dismissed',
                    'reviewed_at': _now,
                    'reviewed_by': admin_email,
                    'action_taken': action,
                    'notes': notes
                }}
            )

            report = report_col.find_one({'_id': report_id},
                {'_id': 0, 'reported_user_id': 1, 'reason': 1})
            if report:
                _upd = user_col.update_one
                _rruid = report['reported_user_id']
                if action == 'warn':
                    _upd(
                        {'id': _rruid},
                        {'$inc': {'moderation_warnings': 1}}
                    )
                elif action == 'suspend':
                    _upd(
                        {'id': _rruid},
                        {'$set': {
                            'account_status': 'suspended',
                            'suspended_until': _now + timedelta(days=7)
                        }}
                    )
                elif action == 'ban':
                    _upd(
                        {'id': _rruid},
                        {'$set': {'account_status': 'banned', 'banned_at': _now}}
                    )

                _rget = report.get
                action_col.insert_one({
                    'report_id': report_id,
                    'user_id': _rget('reported_user_id'),
                    'action': action,
                    'reason': _rget('reason'),
                    'taken_by': admin_email,
                    'created_at': _now
                })

            log.info(f"Report {report_id} reviewed: action={action} by {admin_email}")

            return JsonResponse({
                'success': True,
                'data': {'report_id': str(report_id), 'action': action, 'message': f'Action taken: {action}'}
            })

        except Exception as e:
            log.exception(f'Review error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentModerationView(View):
    """İçerik moderasyonu"""

    def post(self, request):
        """İçeriği modere et"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget = data.get
            content = str(_dget('content', ''))[:5000]
            content_type = str(_dget('content_type', ''))[:50]

            if not content:
                return JsonResponse({'detail': 'content is required'}, status=400)

            content_lower = content.lower()
            flags = [kw for kw in _INAPPROPRIATE_KEYWORDS if kw in content_lower]
            risk_score = min(100, len(flags) * 25)
            is_approved = risk_score < 50

            return JsonResponse({
                'success': True,
                'data': {
                    'content_type': content_type,
                    'risk_score': risk_score,
                    'flags': flags,
                    'is_approved': is_approved,
                    'confidence': 0.85,
                    'recommendation': 'approve' if is_approved else 'review',
                    'timestamp': datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            log.exception(f'Moderation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BanManagementView(View):
    """Ban/Block yönetimi"""

    def get(self, request):
        """Aktif banları listele"""
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            _remove = {'_id': 0, 'password': 0}
            _bf = next(user_col.aggregate([{'$facet': {
                'suspended': [
                    {'$match': {'account_status': 'suspended', 'suspended_until': {'$gt': datetime.utcnow().isoformat()}}},
                    {'$project': _remove}, {'$limit': 50},
                ],
                'banned': [
                    {'$match': {'account_status': 'banned'}},
                    {'$project': _remove}, {'$limit': 50},
                ],
            }}]), {})
            _bfget = _bf.get
            suspended = _bfget('suspended', [])
            banned    = _bfget('banned', [])

            return JsonResponse({
                'success': True,
                'data': {
                    'suspended_count': len(suspended),
                    'banned_count': len(banned),
                    'suspended': suspended[:10],
                    'banned': banned[:10]
                }
            })

        except Exception as e:
            log.exception(f'Ban list error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)

    def post(self, request):
        """Kullanıcıyı ban et"""
        try:
            admin_payload = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _dget2 = data.get
            user_id = _dget2('user_id')
            ban_type = _dget2('ban_type')
            if ban_type not in ('temporary', 'permanent'):
                return JsonResponse({'detail': 'ban_type must be temporary or permanent'}, status=400)
            try:
                duration_days = max(1, int(_dget2('duration_days', 7)))
            except (TypeError, ValueError):
                duration_days = 7
            reason = str(_dget2('reason', ''))[:500]

            if not user_id:
                return JsonResponse({'detail': 'user_id is required'}, status=400)

            _now = datetime.utcnow()
            db = _get_db()
            user_col = db['appfaceapi_myuser']
            ban_col = db['ban_records']

            expires_at = (_now + timedelta(days=duration_days)) if ban_type == 'temporary' else None

            _admin_email = admin_payload.get('email', 'admin')
            ban_col.insert_one({
                'user_id': user_id,
                'ban_type': ban_type,
                'reason': reason,
                'duration_days': duration_days,
                'created_at': _now,
                'created_by': _admin_email,
                'expires_at': expires_at,
            })

            _expires_iso = expires_at.isoformat() if expires_at else None
            user_col.update_one(
                {'id': user_id},
                {'$set': {
                    'account_status': 'banned' if ban_type == 'permanent' else 'suspended',
                    'suspended_until': _expires_iso,
                }}
            )

            log.info(f"User {user_id} {ban_type}-banned by {_admin_email}")

            return JsonResponse({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'ban_type': ban_type,
                    'expires_at': _expires_iso,
                }
            })

        except Exception as e:
            log.exception(f'Ban error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ModerationStatsView(View):
    """Moderasyon istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            report_col = db['user_reports']
            action_col = db['moderation_actions']

            try:
                period_days = min(max(1, int(request.GET.get('period', 30))), 365)
            except (ValueError, TypeError):
                period_days = 30

            start_date = datetime.utcnow() - timedelta(days=period_days)

            _rf = next(report_col.aggregate([{'$facet': {
                'total':    [{'$match': {'created_at': {'$gte': start_date}}},                               {'$count': 'n'}],
                'pending':  [{'$match': {'created_at': {'$gte': start_date}, 'status': 'pending'}},  {'$count': 'n'}],
                'resolved': [{'$match': {'created_at': {'$gte': start_date}, 'status': 'resolved'}}, {'$count': 'n'}],
            }}]), {})
            _rfget = _rf.get
            total_reports    = (_rfget('total',    [{}])[0] or {}).get('n', 0)
            pending_reports  = (_rfget('pending',  [{}])[0] or {}).get('n', 0)
            resolved_reports = (_rfget('resolved', [{}])[0] or {}).get('n', 0)

            _af = next(action_col.aggregate([{'$facet': {
                action_type: [{'$match': {'created_at': {'$gte': start_date}, 'action': action_type}}, {'$count': 'n'}]
                for action_type in _VALID_MOD_ACTIONS
            }}]), {})
            actions = {at: (_af.get(at, [{}])[0] or {}).get('n', 0) for at in _VALID_MOD_ACTIONS}

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': period_days,
                    'total_reports': total_reports,
                    'pending_reports': pending_reports,
                    'resolved_reports': resolved_reports,
                    'actions_taken': actions
                }
            })

        except Exception as e:
            log.exception(f'Stats error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
