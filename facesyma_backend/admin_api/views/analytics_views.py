"""
admin_api/views/analytics_views.py
==================================
Real-time Analytics Dashboard

Features:
  - User growth metrics
  - Revenue analytics
  - Churn analysis
  - Community statistics
  - Compatibility activity
"""

import json
import logging
import time
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
class AnalyticsDashboardView(View):
    """Ana analytics dashboard - overview"""

    def get(self, request):
        try:
            db = _get_db()

            # User metrics
            user_col = db['appfaceapi_myuser']
            total_users = user_col.count_documents({})

            # Son 30 gün yeni kullanıcılar
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_users_30d = user_col.count_documents({
                'date_joined': {'$gte': thirty_days_ago.isoformat()}
            })

            # Community metrics
            community_col = db['communities']
            total_communities = community_col.count_documents({})
            active_communities = community_col.count_documents({
                'is_active': True
            })

            # Subscription metrics
            sub_col = db['user_subscriptions']
            premium_users = sub_col.count_documents({
                'tier': 'premium',
                'status': 'active'
            })
            free_users = total_users - premium_users

            # Calculate MRR (Monthly Recurring Revenue)
            # Assuming $9.99/month per premium user
            mrr = premium_users * 9.99

            # App source breakdown
            web_users = user_col.count_documents({'app_source': 'web'})
            mobile_users = user_col.count_documents({'$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}]})

            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'users': {
                    'total': total_users,
                    'new_30d': new_users_30d,
                    'premium': premium_users,
                    'free': free_users,
                    'premium_percentage': round((premium_users / max(total_users, 1)) * 100, 2)
                },
                'app_breakdown': {  # YENİ
                    'mobile': mobile_users,
                    'web': web_users
                },
                'communities': {
                    'total': total_communities,
                    'active': active_communities,
                    'avg_members': _calculate_avg_community_size(db)
                },
                'revenue': {
                    'mrr': round(mrr, 2),
                    'arr': round(mrr * 12, 2),
                    'currency': 'USD'
                },
                'health': {
                    'services_up': _check_service_health(),
                    'api_uptime': '99.9%',
                    'last_check': datetime.utcnow().isoformat()
                }
            }

            return JsonResponse({'success': True, 'data': dashboard_data})

        except Exception as e:
            log.exception(f'Dashboard hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserGrowthMetricsView(View):
    """Kullanıcı büyüme metrikleri (30 günlük trend)"""

    def get(self, request):
        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            # Son 30 günü günlük veriye böl
            metrics = []
            for day_offset in range(30, -1, -1):
                date = (datetime.utcnow() - timedelta(days=day_offset)).date()
                date_start = datetime(date.year, date.month, date.day)
                date_end = date_start + timedelta(days=1)

                count = user_col.count_documents({
                    'date_joined': {
                        '$gte': date_start.isoformat(),
                        '$lt': date_end.isoformat()
                    }
                })

                metrics.append({
                    'date': date.isoformat(),
                    'new_users': count
                })

            return JsonResponse({
                'success': True,
                'data': {
                    'period': '30_days',
                    'metrics': metrics,
                    'generated_at': datetime.utcnow().isoformat()
                }
            })

        except Exception as e:
            log.exception(f'Growth metrics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RevenueMetricsView(View):
    """Para kazanç metrikleri"""

    def get(self, request):
        try:
            db = _get_db()
            sub_col = db['user_subscriptions']

            # Premium users
            premium_users = sub_col.count_documents({
                'tier': 'premium',
                'status': 'active'
            })

            # MRR hesapla
            mrr = premium_users * 9.99

            # Churn rate (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            canceled_users = sub_col.count_documents({
                'status': 'canceled',
                'canceled_at': {'$gte': thirty_days_ago}
            })

            total_premium_30d = sub_col.count_documents({
                'tier': 'premium'
            })

            churn_rate = (canceled_users / max(total_premium_30d, 1)) * 100

            revenue_data = {
                'mrr': round(mrr, 2),
                'arr': round(mrr * 12, 2),
                'active_premium_users': premium_users,
                'churn_rate': round(churn_rate, 2),
                'churn_users_30d': canceled_users,
                'ltv': round(premium_users * 9.99 * 12, 2),  # Simple LTV calculation
                'currency': 'USD'
            }

            return JsonResponse({
                'success': True,
                'data': revenue_data
            })

        except Exception as e:
            log.exception(f'Revenue metrics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommunityMetricsView(View):
    """Komunite istatistikleri"""

    def get(self, request):
        try:
            db = _get_db()
            comm_col = db['communities']
            member_col = db['community_members']

            total_communities = comm_col.count_documents({})
            active_communities = comm_col.count_documents({'is_active': True})

            # Üye sayıları
            total_members = member_col.count_documents({})
            active_members = member_col.count_documents({'status': 'active'})

            # Ortalama topluluk boyutu
            avg_size = total_members / max(total_communities, 1)

            # En büyük komuniteler
            pipeline = [
                {'$group': {
                    '_id': '$community_id',
                    'member_count': {'$sum': 1}
                }},
                {'$sort': {'member_count': -1}},
                {'$limit': 5}
            ]

            top_communities = list(member_col.aggregate(pipeline))

            metrics = {
                'total_communities': total_communities,
                'active_communities': active_communities,
                'total_members': total_members,
                'active_members': active_members,
                'avg_community_size': round(avg_size, 2),
                'top_5_communities': top_communities
            }

            return JsonResponse({
                'success': True,
                'data': metrics
            })

        except Exception as e:
            log.exception(f'Community metrics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CompatibilityMetricsView(View):
    """Uyumluluk check istatistikleri"""

    def get(self, request):
        try:
            db = _get_db()
            compat_col = db['compatibility']

            total_checks = compat_col.count_documents({})

            # Category breakdown
            categories = {}
            for cat in ['UYUMLU', 'UYUMSUZ', 'SAME_CATEGORY', 'DIFFERENT_CATEGORY']:
                categories[cat] = compat_col.count_documents({'category': cat})

            # Average compatibility score
            avg_score_result = list(compat_col.aggregate([
                {'$group': {
                    '_id': None,
                    'avg_score': {'$avg': '$score'}
                }}
            ]))

            avg_score = avg_score_result[0]['avg_score'] if avg_score_result else 0

            metrics = {
                'total_checks': total_checks,
                'average_score': round(avg_score, 2),
                'categories': categories,
                'high_compatibility_count': compat_col.count_documents({'score': {'$gte': 70}}),
                'low_compatibility_count': compat_col.count_documents({'score': {'$lt': 30}})
            }

            return JsonResponse({
                'success': True,
                'data': metrics
            })

        except Exception as e:
            log.exception(f'Compatibility metrics hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


def _calculate_avg_community_size(db):
    """Ortalama komunite boyutunu hesapla"""
    try:
        member_col = db['community_members']
        comm_col = db['communities']

        total_members = member_col.count_documents({})
        total_communities = comm_col.count_documents({})

        if total_communities == 0:
            return 0

        return round(total_members / total_communities, 2)
    except:
        return 0


def _check_service_health():
    """Service sağlığını kontrol et"""
    try:
        db = _get_db()
        # MongoDB bağlantısı test et
        db.command('ping')
        return {
            'mongodb': 'up',
            'api': 'up',
            'chat_service': 'up'
        }
    except:
        return {
            'mongodb': 'down',
            'api': 'up',
            'chat_service': 'unknown'
        }


@method_decorator(csrf_exempt, name='dispatch')
class AnalysisActivityView(View):
    """Face analiz aktivitesi istatistikleri"""

    def get(self, request):
        try:
            from admin_api.utils.mongo import get_history_col

            history_col = get_history_col()

            # Toplam analiz sayısı
            total_analyses = history_col.count_documents({})

            # Son 7 gün ve 30 gün (created_at Unix float olduğu için)
            now_ts = time.time()
            last_7d = history_col.count_documents({
                'created_at': {'$gte': now_ts - (7 * 24 * 3600)}
            })
            last_30d = history_col.count_documents({
                'created_at': {'$gte': now_ts - (30 * 24 * 3600)}
            })

            # Mode'a göre dağılım
            mode_breakdown = {}
            for mode in ['character', 'enhanced_character', 'modules', 'golden', 'face_type', 'art', 'astrology', 'advisor', 'daily', 'golden_transform']:
                count = history_col.count_documents({'mode': mode})
                if count > 0:
                    mode_breakdown[mode] = count

            # Son 7 günün günlük trend (Unix float kullanarak)
            daily_trend = []
            now_dt = datetime.utcnow()
            for day_offset in range(7, -1, -1):
                date = (now_dt - timedelta(days=day_offset)).date()
                date_start_ts = time.mktime((date.year, date.month, date.day, 0, 0, 0, 0, 0, -1)) + (time.timezone if time.daylight == 0 else time.altzone)
                date_end_ts = date_start_ts + 86400

                count = history_col.count_documents({
                    'created_at': {
                        '$gte': date_start_ts,
                        '$lt': date_end_ts
                    }
                })

                daily_trend.append({
                    'date': date.isoformat(),
                    'count': count
                })

            # App source breakdown
            base_query = {}
            web_analyses = history_col.count_documents({**base_query, 'app_source': 'web'})
            mobile_analyses = history_col.count_documents({**base_query, '$or': [{'app_source': {'$exists': False}}, {'app_source': {'$ne': 'web'}}]})

            return JsonResponse({
                'success': True,
                'data': {
                    'total_analyses': total_analyses,
                    'last_7d': last_7d,
                    'last_30d': last_30d,
                    'by_mode': mode_breakdown,
                    'app_breakdown': {  # YENİ
                        'mobile': mobile_analyses,
                        'web': web_analyses
                    },
                    'daily_trend': daily_trend
                }
            })

        except Exception as e:
            log.exception(f'Analysis activity hatası: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
