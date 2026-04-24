"""
admin_api/views/retention_views.py
==================================
Retention & Cohort Analysis
"""

import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class CohortAnalysisView(View):
    """Cohort analizi - gruplara göre retention"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            _now = datetime.utcnow()
            today = _now.date()
            window_start_iso = (today - timedelta(weeks=12)).isoformat()
            seven_days_ago = _now - timedelta(days=7)

            # Combined $facet: one pass over users joined in the 12-week window
            _rc = next(user_col.aggregate([
                {'$match': {'date_joined': {'$gte': window_start_iso}}},
                {'$facet': {
                    'signups': [{'$group': {'_id': {'$substr': ['$date_joined', 0, 10]}, 'count': {'$sum': 1}}}],
                    'active':  [{'$match': {'last_active_at': {'$gte': seven_days_ago}}},
                                {'$group': {'_id': {'$substr': ['$date_joined', 0, 10]}, 'count': {'$sum': 1}}}],
                }}
            ]), {})
            signup_by_date = {doc['_id']: doc['count'] for doc in _rc.get('signups', [])}
            active_by_date = {doc['_id']: doc['count'] for doc in _rc.get('active',  [])}

            cohorts = {}
            for week in range(12):
                week_start = today - timedelta(weeks=week, days=today.weekday())
                week_signups = sum(signup_by_date.get((week_start + timedelta(days=d)).isoformat(), 0) for d in range(7))
                week_active = sum(active_by_date.get((week_start + timedelta(days=d)).isoformat(), 0) for d in range(7))
                cohorts[week_start.isoformat()] = {
                    'signups': week_signups,
                    'active': week_active,
                    'retention_rate': round((week_active / max(week_signups, 1)) * 100, 2)
                }

            return JsonResponse({
                'success': True,
                'data': {'cohorts': cohorts, 'analysis_date': today.isoformat()}
            })

        except Exception as e:
            log.exception(f'Cohort analysis error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RetentionCurveView(View):
    """Retention curve - zaman içinde retention"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']

            _now = datetime.utcnow()
            thirty_days_ago = _now - timedelta(days=30)

            # Single aggregation: active users per day over last 30 days
            active_by_date = {
                doc['_id']: doc['count']
                for doc in user_col.aggregate([
                    {'$match': {'last_active_at': {'$gte': thirty_days_ago}}},
                    {'$group': {
                        '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$last_active_at'}},
                        'count': {'$sum': 1}
                    }}
                ])
            }

            retention_curve = []
            _abdget = active_by_date.get
            for day in range(30):
                date = (_now - timedelta(days=day)).date()
                _ds = date.isoformat()
                active_today = _abdget(_ds, 0)
                active_prev = _abdget((date - timedelta(days=1)).isoformat(), 0)
                retention_pct = (active_today / max(active_prev, 1)) * 100
                retention_curve.append({
                    'date': _ds,
                    'active_users': active_today,
                    'retention': round(retention_pct, 2),
                })

            return JsonResponse({'success': True, 'data': {'period_days': 30, 'curve': retention_curve}})

        except Exception as e:
            log.exception(f'Retention curve error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChurnPredictionView(View):
    """Churn riski tahmin etme"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']
            now = datetime.utcnow()

            fourteen_days_ago = now - timedelta(days=14)
            seven_days_ago = now - timedelta(days=7)
            _risk = next(user_col.aggregate([{'$group': {'_id': None,
                'high_risk':   {'$sum': {'$cond': [{'$lt':  ['$last_active_at', fourteen_days_ago]}, 1, 0]}},
                'medium_risk': {'$sum': {'$cond': [{'$and': [
                    {'$gte': ['$last_active_at', fourteen_days_ago]},
                    {'$lt':  ['$last_active_at', seven_days_ago]}
                ]}, 1, 0]}},
                'low_risk':    {'$sum': {'$cond': [{'$gte': ['$last_active_at', seven_days_ago]}, 1, 0]}},
            }}]), {'high_risk': 0, 'medium_risk': 0, 'low_risk': 0})
            high_risk = _risk['high_risk']
            medium_risk = _risk['medium_risk']
            low_risk = _risk['low_risk']
            total = max(high_risk + medium_risk + low_risk, 1)

            return JsonResponse({
                'success': True,
                'data': {
                    'high_risk': {'count': high_risk, 'percentage': round(high_risk / total * 100, 2), 'recommendation': 'Re-engagement campaign needed'},
                    'medium_risk': {'count': medium_risk, 'percentage': round(medium_risk / total * 100, 2), 'recommendation': 'Remind users with notifications'},
                    'low_risk': {'count': low_risk, 'percentage': round(low_risk / total * 100, 2), 'recommendation': 'Maintain engagement'}
                }
            })

        except Exception as e:
            log.exception(f'Churn prediction error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserFunnelView(View):
    """Kullanıcı funnel analizi"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']
            history_col = db['analysis_history']
            conv_col = db['ai_conversations']
            comm_col = db['community_members']

            step1_signups = user_col.estimated_document_count()
            step2_analyzed = history_col.estimated_document_count()
            step3_chatted = conv_col.estimated_document_count()
            step4_communities = comm_col.estimated_document_count()

            funnel = [
                {'step': 1, 'name': 'Sign Up', 'count': step1_signups, 'conversion': 100.0},
                {'step': 2, 'name': 'Face Analysis', 'count': step2_analyzed, 'conversion': round((step2_analyzed / max(step1_signups, 1)) * 100, 2)},
                {'step': 3, 'name': 'Chat', 'count': step3_chatted, 'conversion': round((step3_chatted / max(step2_analyzed, 1)) * 100, 2)},
                {'step': 4, 'name': 'Community Join', 'count': step4_communities, 'conversion': round((step4_communities / max(step3_chatted, 1)) * 100, 2)},
            ]

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
            log.exception(f'Funnel analysis error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BehaviorSegmentationView(View):
    """Kullanıcı davranış segmentasyonu"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            user_col = db['appfaceapi_myuser']
            now = datetime.utcnow()

            seven_ago = now - timedelta(days=7)
            fourteen_ago = now - timedelta(days=14)
            thirty_ago = now - timedelta(days=30)
            _seg = next(user_col.aggregate([{'$group': {'_id': None,
                'total':   {'$sum': 1},
                'active':  {'$sum': {'$cond': [{'$gte': ['$last_active_at', seven_ago]}, 1, 0]}},
                'dormant': {'$sum': {'$cond': [{'$and': [
                    {'$gte': ['$last_active_at', thirty_ago]},
                    {'$lt':  ['$last_active_at', fourteen_ago]}
                ]}, 1, 0]}},
                'churned': {'$sum': {'$cond': [{'$lt': ['$last_active_at', thirty_ago]}, 1, 0]}},
            }}]), {'total': 0, 'active': 0, 'dormant': 0, 'churned': 0})
            total_users = _seg['total']
            active_segment = _seg['active']
            dormant_segment = _seg['dormant']
            churned_segment = _seg['churned']

            premium_col = db['user_subscriptions']
            premium_active = premium_col.count_documents({'tier': 'premium', 'status': 'active'})

            return JsonResponse({
                'success': True,
                'data': {
                    'total_users': total_users,
                    'segments': {
                        'active': {'count': active_segment, 'percentage': round(active_segment / max(total_users, 1) * 100, 2), 'color': 'green'},
                        'dormant': {'count': dormant_segment, 'percentage': round(dormant_segment / max(total_users, 1) * 100, 2), 'color': 'yellow'},
                        'churned': {'count': churned_segment, 'percentage': round(churned_segment / max(total_users, 1) * 100, 2), 'color': 'red'},
                        'premium': {'count': premium_active, 'percentage': round(premium_active / max(total_users, 1) * 100, 2), 'color': 'gold'},
                    }
                }
            })

        except Exception as e:
            log.exception(f'Segmentation error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
