"""
admin_api/views/retention_views.py
==================================
Retention & Cohort Analysis

Features:
  - Cohort analysis
  - Retention curves
  - Churn prediction
  - User behavior funnels
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
class CohortAnalysisView(View):
    """Cohort analizi - gruplara göre retention"""

    def get(self, request):
        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            # Cohortları oluştur (haftalık)
            cohorts = {}
            today = datetime.utcnow().date()

            # Son 12 haftanın cohortlarını oluştur
            for week in range(12):
                week_start = today - timedelta(weeks=week, days=today.weekday())
                week_end = week_start + timedelta(days=7)

                # Bu haftada sign up olan users
                users_in_week = user_col.count_documents({
                    'date_joined': {
                        '$gte': datetime(week_start.year, week_start.month, week_start.day).isoformat(),
                        '$lt': datetime(week_end.year, week_end.month, week_end.day).isoformat()
                    }
                })

                # Bu haftadan sonra active olan users
                active_users = user_col.count_documents({
                    'date_joined': {
                        '$gte': datetime(week_start.year, week_start.month, week_start.day).isoformat(),
                        '$lt': datetime(week_end.year, week_end.month, week_end.day).isoformat()
                    },
                    'last_active_at': {'$gte': datetime.utcnow() - timedelta(days=7)}
                })

                retention_rate = (active_users / max(users_in_week, 1)) * 100

                cohorts[week_start.isoformat()] = {
                    'signups': users_in_week,
                    'active': active_users,
                    'retention_rate': round(retention_rate, 2)
                }

            return JsonResponse({
                'success': True,
                'data': {
                    'cohorts': cohorts,
                    'analysis_date': today.isoformat()
                }
            })

        except Exception as e:
            log.exception(f'Cohort analysis hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RetentionCurveView(View):
    """Retention curve - zaman içinde retention"""

    def get(self, request):
        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            # Son 30 gün için günlük retention
            retention_curve = []

            for day in range(30):
                date = (datetime.utcnow() - timedelta(days=day)).date()
                date_start = datetime(date.year, date.month, date.day)
                date_end = date_start + timedelta(days=1)

                # Bu gün active olan users
                active_today = user_col.count_documents({
                    'last_active_at': {
                        '$gte': date_start,
                        '$lt': date_end
                    }
                })

                # Dün de active olan users (return)
                active_yesterday = user_col.count_documents({
                    'last_active_at': {'$gte': date_start - timedelta(days=1)}
                })

                retention_pct = (active_today / max(active_yesterday, 1)) * 100

                retention_curve.append({
                    'date': date.isoformat(),
                    'active_users': active_today,
                    'retention': round(retention_pct, 2)
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'period_days': 30,
                    'curve': retention_curve
                }
            })

        except Exception as e:
            log.exception(f'Retention curve hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChurnPredictionView(View):
    """Churn riski tahmin etme"""

    def get(self, request):
        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            # Risk kategorileri
            now = datetime.utcnow()

            # High risk: 14+ gün inaktif
            high_risk = user_col.count_documents({
                'last_active_at': {'$lt': now - timedelta(days=14)}
            })

            # Medium risk: 7-14 gün inaktif
            medium_risk = user_col.count_documents({
                'last_active_at': {
                    '$gte': now - timedelta(days=14),
                    '$lt': now - timedelta(days=7)
                }
            })

            # Low risk: 0-7 gün inaktif
            low_risk = user_col.count_documents({
                'last_active_at': {'$gte': now - timedelta(days=7)}
            })

            prediction = {
                'high_risk': {
                    'count': high_risk,
                    'percentage': round((high_risk / max(high_risk + medium_risk + low_risk, 1)) * 100, 2),
                    'recommendation': 'Re-engagement campaign needed'
                },
                'medium_risk': {
                    'count': medium_risk,
                    'percentage': round((medium_risk / max(high_risk + medium_risk + low_risk, 1)) * 100, 2),
                    'recommendation': 'Remind users with notifications'
                },
                'low_risk': {
                    'count': low_risk,
                    'percentage': round((low_risk / max(high_risk + medium_risk + low_risk, 1)) * 100, 2),
                    'recommendation': 'Maintain engagement'
                }
            }

            return JsonResponse({
                'success': True,
                'data': prediction
            })

        except Exception as e:
            log.exception(f'Churn prediction hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserFunnelView(View):
    """Kullanıcı funnel analizi"""

    def get(self, request):
        try:
            db = _get_db()

            # Conversion funnel: Sign up → Analyze → Chat → Community
            user_col = db['appfaceapi_myuser']
            history_col = db['analysis_history']
            conv_col = db['ai_conversations']
            comm_col = db['community_members']

            step1_signups = user_col.count_documents({})

            step2_analyzed = history_col.count_documents({})

            step3_chatted = conv_col.count_documents({})

            step4_communities = comm_col.count_documents({})

            funnel = [
                {
                    'step': 1,
                    'name': 'Sign Up',
                    'count': step1_signups,
                    'conversion': 100.0
                },
                {
                    'step': 2,
                    'name': 'Face Analysis',
                    'count': step2_analyzed,
                    'conversion': round((step2_analyzed / max(step1_signups, 1)) * 100, 2)
                },
                {
                    'step': 3,
                    'name': 'Chat',
                    'count': step3_chatted,
                    'conversion': round((step3_chatted / max(step2_analyzed, 1)) * 100, 2)
                },
                {
                    'step': 4,
                    'name': 'Community Join',
                    'count': step4_communities,
                    'conversion': round((step4_communities / max(step3_chatted, 1)) * 100, 2)
                }
            ]

            # Calculate drop-off
            total_dropoff = step1_signups - step4_communities
            dropoff_pct = (total_dropoff / max(step1_signups, 1)) * 100

            return JsonResponse({
                'success': True,
                'data': {
                    'funnel': funnel,
                    'total_dropoff': total_dropoff,
                    'dropoff_percentage': round(dropoff_pct, 2),
                    'completion_rate': round((step4_communities / max(step1_signups, 1)) * 100, 2)
                }
            })

        except Exception as e:
            log.exception(f'Funnel analysis hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BehaviorSegmentationView(View):
    """Kullanıcı davranış segmentasyonu"""

    def get(self, request):
        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            # Segmentleri oluştur
            now = datetime.utcnow()

            # Active users (last 7 days)
            active_segment = user_col.count_documents({
                'last_active_at': {'$gte': now - timedelta(days=7)}
            })

            # Dormant (14-30 days)
            dormant_segment = user_col.count_documents({
                'last_active_at': {
                    '$gte': now - timedelta(days=30),
                    '$lt': now - timedelta(days=14)
                }
            })

            # Churned (30+ days)
            churned_segment = user_col.count_documents({
                'last_active_at': {'$lt': now - timedelta(days=30)}
            })

            # Premium users
            premium_col = db['user_subscriptions']
            premium_active = premium_col.count_documents({
                'tier': 'premium',
                'status': 'active'
            })

            total_users = user_col.count_documents({})

            segments = {
                'active': {
                    'count': active_segment,
                    'percentage': round((active_segment / max(total_users, 1)) * 100, 2),
                    'color': 'green'
                },
                'dormant': {
                    'count': dormant_segment,
                    'percentage': round((dormant_segment / max(total_users, 1)) * 100, 2),
                    'color': 'yellow'
                },
                'churned': {
                    'count': churned_segment,
                    'percentage': round((churned_segment / max(total_users, 1)) * 100, 2),
                    'color': 'red'
                },
                'premium': {
                    'count': premium_active,
                    'percentage': round((premium_active / max(total_users, 1)) * 100, 2),
                    'color': 'gold'
                }
            }

            return JsonResponse({
                'success': True,
                'data': {
                    'total_users': total_users,
                    'segments': segments
                }
            })

        except Exception as e:
            log.exception(f'Segmentation hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
