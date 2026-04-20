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
from pymongo import MongoClient
from django.conf import settings

log = logging.getLogger(__name__)


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


@method_decorator(csrf_exempt, name='dispatch')
class UserReportsView(View):
    """Kullanıcı şikayet yönetimi"""

    def get(self, request):
        """Şikayetleri listele"""
        try:
            db = _get_db()
            report_col = db['user_reports']

            status = request.GET.get('status', None)  # pending, reviewed, resolved, dismissed
            limit = int(request.GET.get('limit', 50))

            query = {}
            if status:
                query['status'] = status

            reports = list(report_col.find(query)
                          .sort('created_at', -1)
                          .limit(limit))

            for r in reports:
                r['_id'] = str(r['_id'])

            return JsonResponse({
                'success': True,
                'data': {
                    'total': report_col.count_documents(query),
                    'limit': limit,
                    'reports': reports
                }
            })

        except Exception as e:
            log.exception(f'Reports list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Yeni şikayet oluştur"""
        try:
            data = json.loads(request.body)

            db = _get_db()
            report_col = db['user_reports']

            report = {
                'reporter_id': data.get('reporter_id'),
                'reported_user_id': data.get('reported_user_id'),
                'report_type': data.get('report_type'),  # harassment, spam, inappropriate, other
                'content_type': data.get('content_type'),  # message, profile, comment
                'content_id': data.get('content_id'),
                'reason': data.get('reason'),
                'description': data.get('description'),
                'status': 'pending',
                'severity': 'medium',
                'created_at': datetime.utcnow(),
                'reviewed_at': None,
                'reviewed_by': None,
                'action_taken': None
            }

            result = report_col.insert_one(report)

            log.info(f"User report created: {result.inserted_id}")

            return JsonResponse({
                'success': True,
                'data': {
                    'report_id': str(result.inserted_id),
                    'status': 'pending'
                }
            })

        except Exception as e:
            log.exception(f'Report creation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReportReviewView(View):
    """Şikayet gözden geçirme ve işlem"""

    def post(self, request):
        """Şikayeti gözden geçir ve karar ver"""
        try:
            data = json.loads(request.body)
            report_id = data.get('report_id')
            action = data.get('action')  # dismiss, warn, suspend, ban
            notes = data.get('notes')

            db = _get_db()
            report_col = db['user_reports']
            user_col = db['users']
            action_col = db['moderation_actions']

            # Report'u güncelle
            report_col.update_one(
                {'_id': report_id},
                {'$set': {
                    'status': 'resolved' if action != 'dismiss' else 'dismissed',
                    'reviewed_at': datetime.utcnow(),
                    'reviewed_by': request.user.id if hasattr(request, 'user') else 'system',
                    'action_taken': action,
                    'notes': notes
                }}
            )

            # Eğer action varsa, user'a işlem uygula
            report = report_col.find_one({'_id': report_id})

            if action == 'warn':
                user_col.update_one(
                    {'user_id': report['reported_user_id']},
                    {'$inc': {'moderation_warnings': 1}}
                )

            elif action == 'suspend':
                user_col.update_one(
                    {'user_id': report['reported_user_id']},
                    {'$set': {
                        'account_status': 'suspended',
                        'suspended_until': datetime.utcnow() + timedelta(days=7)
                    }}
                )

            elif action == 'ban':
                user_col.update_one(
                    {'user_id': report['reported_user_id']},
                    {'$set': {
                        'account_status': 'banned',
                        'banned_at': datetime.utcnow()
                    }}
                )

            # Log the action
            action_col.insert_one({
                'report_id': report_id,
                'user_id': report['reported_user_id'],
                'action': action,
                'reason': report.get('reason'),
                'taken_by': request.user.id if hasattr(request, 'user') else 'system',
                'created_at': datetime.utcnow()
            })

            log.info(f"Report {report_id} reviewed: action={action}")

            return JsonResponse({
                'success': True,
                'data': {
                    'report_id': report_id,
                    'action': action,
                    'message': f'Action taken: {action}'
                }
            })

        except Exception as e:
            log.exception(f'Review hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ContentModerationView(View):
    """İçerik moderasyonu (AI-powered)"""

    def post(self, request):
        """İçeriği modere et"""
        try:
            data = json.loads(request.body)
            content = data.get('content')
            content_type = data.get('content_type')  # message, post, profile_bio

            # Basit keyword-based filtering (production'da ML model kullan)
            inappropriate_keywords = [
                'spam', 'abuse', 'hate', 'violence', 'porn'
            ]

            content_lower = content.lower()

            flags = []
            for keyword in inappropriate_keywords:
                if keyword in content_lower:
                    flags.append(keyword)

            risk_score = len(flags) * 25  # 0-100
            is_approved = risk_score < 50

            moderation_result = {
                'content': content,
                'content_type': content_type,
                'risk_score': risk_score,
                'flags': flags,
                'is_approved': is_approved,
                'confidence': 0.85,
                'recommendation': 'approve' if is_approved else 'review',
                'timestamp': datetime.utcnow().isoformat()
            }

            return JsonResponse({
                'success': True,
                'data': moderation_result
            })

        except Exception as e:
            log.exception(f'Moderation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BanManagementView(View):
    """Ban/Block yönetimi"""

    def get(self, request):
        """Aktif banları listele"""
        try:
            db = _get_db()
            user_col = db['users']

            # Suspended users
            suspended = list(user_col.find({
                'account_status': 'suspended',
                'suspended_until': {'$gt': datetime.utcnow()}
            }).limit(50))

            # Banned users
            banned = list(user_col.find({
                'account_status': 'banned'
            }).limit(50))

            return JsonResponse({
                'success': True,
                'data': {
                    'suspended_users': len(suspended),
                    'banned_users': len(banned),
                    'suspended': suspended[:10],
                    'banned': banned[:10]
                }
            })

        except Exception as e:
            log.exception(f'Ban list hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)

    def post(self, request):
        """Kullanıcıyı ban et"""
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            ban_type = data.get('ban_type')  # temporary, permanent
            duration_days = data.get('duration_days', 7)
            reason = data.get('reason')

            db = _get_db()
            user_col = db['users']
            ban_col = db['ban_records']

            # Ban kaydı oluştur
            ban_record = {
                'user_id': user_id,
                'ban_type': ban_type,
                'reason': reason,
                'duration_days': duration_days,
                'created_at': datetime.utcnow(),
                'created_by': request.user.id if hasattr(request, 'user') else 'system',
                'expires_at': datetime.utcnow() + timedelta(days=duration_days) if ban_type == 'temporary' else None
            }

            ban_col.insert_one(ban_record)

            # User'ı ban et
            user_col.update_one(
                {'user_id': user_id},
                {'$set': {
                    'account_status': 'banned' if ban_type == 'permanent' else 'suspended',
                    'suspended_until': ban_record['expires_at']
                }}
            )

            log.info(f"User {user_id} banned: {ban_type}")

            return JsonResponse({
                'success': True,
                'data': {
                    'user_id': user_id,
                    'ban_type': ban_type,
                    'expires_at': ban_record['expires_at'].isoformat() if ban_record['expires_at'] else None
                }
            })

        except Exception as e:
            log.exception(f'Ban hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ModerationStatsView(View):
    """Moderasyon istatistikleri"""

    def get(self, request):
        try:
            db = _get_db()
            report_col = db['user_reports']
            action_col = db['moderation_actions']

            period = request.GET.get('period', '30')
            period_days = int(period)

            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Reports by status
            total_reports = report_col.count_documents({
                'created_at': {'$gte': start_date}
            })
            pending_reports = report_col.count_documents({
                'created_at': {'$gte': start_date},
                'status': 'pending'
            })
            resolved_reports = report_col.count_documents({
                'created_at': {'$gte': start_date},
                'status': 'resolved'
            })

            # Actions taken
            actions = {}
            for action_type in ['warn', 'suspend', 'ban', 'dismiss']:
                count = action_col.count_documents({
                    'created_at': {'$gte': start_date},
                    'action': action_type
                })
                actions[action_type] = count

            # Average response time
            avg_response_time = 0
            responses = list(report_col.aggregate([
                {'$match': {
                    'created_at': {'$gte': start_date},
                    'reviewed_at': {'$exists': True}
                }},
                {'$project': {
                    'response_time_hours': {
                        '$divide': [
                            {'$subtract': ['$reviewed_at', '$created_at']},
                            3600000
                        ]
                    }
                }},
                {'$group': {
                    '_id': None,
                    'avg': {'$avg': '$response_time_hours'}
                }}
            ]))

            if responses:
                avg_response_time = responses[0]['avg']

            stats = {
                'period_days': period_days,
                'total_reports': total_reports,
                'pending_reports': pending_reports,
                'resolved_reports': resolved_reports,
                'avg_response_time_hours': round(avg_response_time, 2),
                'actions_taken': actions
            }

            return JsonResponse({
                'success': True,
                'data': stats
            })

        except Exception as e:
            log.exception(f'Stats hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
