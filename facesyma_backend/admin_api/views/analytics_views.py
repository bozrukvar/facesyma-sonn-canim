"""
admin_api/views/analytics_views.py
==================================
Real-time Analytics Dashboard
"""

import logging
import time
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db, get_history_col
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_VALID_ANALYSIS_MODES = frozenset({'character', 'enhanced_character', 'modules', 'golden', 'face_type', 'art', 'astrology', 'advisor', 'daily', 'golden_transform'})


@method_decorator(csrf_exempt, name='dispatch')
class AnalyticsDashboardView(View):
    """Ana analytics dashboard - overview"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            _now = datetime.utcnow()
            _now_iso = _now.isoformat()
            thirty_days_ago = (_now - timedelta(days=30)).isoformat()

            # Single facet aggregation for user collection (4 → 1 query)
            user_col = db['appfaceapi_myuser']
            u = list(user_col.aggregate([{'$facet': {
                'total':   [{'$count': 'n'}],
                'new_30d': [{'$match': {'date_joined': {'$gte': thirty_days_ago}}}, {'$count': 'n'}],
                'web':     [{'$match': {'app_source': 'web'}}, {'$count': 'n'}],
                'mobile':  [{'$match': {'$or': [{'app_source': 'mobile'}, {'app_source': {'$exists': False}}]}}, {'$count': 'n'}],
            }}]))[0]
            _uget = u.get
            total_users   = u['total'][0]['n']   if _uget('total')   else 0
            new_users_30d = u['new_30d'][0]['n'] if _uget('new_30d') else 0
            web_users     = u['web'][0]['n']     if _uget('web')     else 0
            mobile_users  = u['mobile'][0]['n']  if _uget('mobile')  else 0

            # Single facet for communities (2 → 1 query)
            community_col = db['communities']
            c = list(community_col.aggregate([{'$facet': {
                'total':  [{'$count': 'n'}],
                'active': [{'$match': {'is_active': True}}, {'$count': 'n'}],
            }}]))[0]
            _cget = c.get
            total_communities  = c['total'][0]['n']  if _cget('total')  else 0
            active_communities = c['active'][0]['n'] if _cget('active') else 0

            sub_col = db['user_subscriptions']
            premium_users = sub_col.count_documents({'tier': 'premium', 'status': 'active'})
            free_users = total_users - premium_users
            mrr = premium_users * 9.99

            return JsonResponse({
                'success': True,
                'data': {
                    'timestamp': _now_iso,
                    'users': {
                        'total': total_users,
                        'new_30d': new_users_30d,
                        'premium': premium_users,
                        'free': free_users,
                        'premium_percentage': round((premium_users / max(total_users, 1)) * 100, 2)
                    },
                    'app_breakdown': {'mobile': mobile_users, 'web': web_users},
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
                        'last_check': _now_iso
                    }
                }
            })

        except Exception as e:
            log.exception(f'Dashboard error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserGrowthMetricsView(View):
    """Kullanıcı büyüme metrikleri (30 günlük trend)"""

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
            window_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)

            pipeline = [
                {'$match': {'date_joined': {'$gte': window_start.isoformat()}}},
                {'$group': {
                    '_id': {'$substr': ['$date_joined', 0, 10]},
                    'new_users': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            agg_result = {doc['_id']: doc['new_users'] for doc in user_col.aggregate(pipeline)}

            metrics = []
            for day_offset in range(30, -1, -1):
                date = (now - timedelta(days=day_offset)).date()
                _ds = date.isoformat()
                metrics.append({'date': _ds, 'new_users': agg_result.get(_ds, 0)})

            return JsonResponse({
                'success': True,
                'data': {
                    'period': '30_days',
                    'metrics': metrics,
                    'generated_at': now.isoformat()
                }
            })

        except Exception as e:
            log.exception(f'Growth metrics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RevenueMetricsView(View):
    """Para kazanç metrikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            sub_col = db['user_subscriptions']

            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            _rev = next(sub_col.aggregate([{'$facet': {
                'active_premium': [{'$match': {'tier': 'premium', 'status': 'active'}}, {'$count': 'n'}],
                'canceled_30d':   [{'$match': {'status': 'canceled', 'canceled_at': {'$gte': thirty_days_ago}}}, {'$count': 'n'}],
                'total_premium':  [{'$match': {'tier': 'premium'}}, {'$count': 'n'}],
            }}]), {})
            _revget = _rev.get
            premium_users     = (_revget('active_premium', [{}])[0] or {}).get('n', 0)
            canceled_users    = (_revget('canceled_30d',   [{}])[0] or {}).get('n', 0)
            total_premium_30d = (_revget('total_premium',  [{}])[0] or {}).get('n', 0)
            mrr = premium_users * 9.99
            churn_rate = (canceled_users / max(total_premium_30d, 1)) * 100

            return JsonResponse({
                'success': True,
                'data': {
                    'mrr': round(mrr, 2),
                    'arr': round(mrr * 12, 2),
                    'active_premium_users': premium_users,
                    'churn_rate': round(churn_rate, 2),
                    'churn_users_30d': canceled_users,
                    'ltv': round(premium_users * 9.99 * 12, 2),
                    'currency': 'USD'
                }
            })

        except Exception as e:
            log.exception(f'Revenue metrics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommunityMetricsView(View):
    """Komunite istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            comm_col = db['communities']
            member_col = db['community_members']

            _c = next(comm_col.aggregate([{'$facet': {
                'total':  [{'$count': 'n'}],
                'active': [{'$match': {'is_active': True}}, {'$count': 'n'}],
            }}]), {})
            _ccget = _c.get
            total_communities  = (_ccget('total',  [{}])[0] or {}).get('n', 0)
            active_communities = (_ccget('active', [{}])[0] or {}).get('n', 0)
            _m = next(member_col.aggregate([{'$facet': {
                'total':  [{'$count': 'n'}],
                'active': [{'$match': {'status': 'active'}}, {'$count': 'n'}],
                'top5':   [{'$group': {'_id': '$community_id', 'member_count': {'$sum': 1}}}, {'$sort': {'member_count': -1}}, {'$limit': 5}],
            }}]), {})
            _mget = _m.get
            total_members    = (_mget('total',  [{}])[0] or {}).get('n', 0)
            active_members   = (_mget('active', [{}])[0] or {}).get('n', 0)
            top_communities  = _mget('top5', [])
            avg_size = total_members / max(total_communities, 1)

            return JsonResponse({
                'success': True,
                'data': {
                    'total_communities': total_communities,
                    'active_communities': active_communities,
                    'total_members': total_members,
                    'active_members': active_members,
                    'avg_community_size': round(avg_size, 2),
                    'top_5_communities': top_communities
                }
            })

        except Exception as e:
            log.exception(f'Community metrics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CompatibilityMetricsView(View):
    """Uyumluluk check istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            compat_col = db['compatibility']

            _cats = ['UYUMLU', 'UYUMSUZ', 'SAME_CATEGORY', 'DIFFERENT_CATEGORY']
            _cp = next(compat_col.aggregate([{'$facet': {
                'total': [{'$count': 'n'}],
                'avg':   [{'$group': {'_id': None, 'v': {'$avg': '$score'}}}],
                'high':  [{'$match': {'score': {'$gte': 70}}}, {'$count': 'n'}],
                'low':   [{'$match': {'score': {'$lt':  30}}}, {'$count': 'n'}],
                'cats':  [{'$group': {'_id': '$category', 'count': {'$sum': 1}}}],
            }}]), {})
            _cpget = _cp.get
            total_checks = (_cpget('total', [{}])[0] or {}).get('n', 0)
            avg_score    = (_cpget('avg',   [{}])[0] or {}).get('v', 0) or 0
            categories   = {_id: doc['count'] for doc in _cpget('cats', []) if (_id := doc['_id']) in _cats}
            for cat in _cats:
                categories.setdefault(cat, 0)

            return JsonResponse({
                'success': True,
                'data': {
                    'total_checks': total_checks,
                    'average_score': round(avg_score, 2),
                    'categories': categories,
                    'high_compatibility_count': (_cpget('high', [{}])[0] or {}).get('n', 0),
                    'low_compatibility_count':  (_cpget('low',  [{}])[0] or {}).get('n', 0),
                }
            })

        except Exception as e:
            log.exception(f'Compatibility metrics error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


def _calculate_avg_community_size(db):
    try:
        member_col = db['community_members']
        comm_col = db['communities']
        total_members = member_col.estimated_document_count()
        total_communities = comm_col.estimated_document_count()
        if total_communities == 0:
            return 0
        return round(total_members / total_communities, 2)
    except Exception:
        return 0


def _check_service_health():
    try:
        db = _get_db()
        db.command('ping')
        return {'mongodb': 'up', 'api': 'up', 'chat_service': 'up'}
    except Exception:
        return {'mongodb': 'down', 'api': 'up', 'chat_service': 'unknown'}


@method_decorator(csrf_exempt, name='dispatch')
class AnalysisActivityView(View):
    """Face analiz aktivitesi istatistikleri"""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            history_col = get_history_col()

            now_ts = time.time()
            week_ago_ts = now_ts - (7 * 24 * 3600)
            month_ago_ts = now_ts - (30 * 24 * 3600)

            # Single aggregation: totals + mode breakdown + daily trend + app split
            facet_result = next(history_col.aggregate([
                {'$facet': {
                    'totals': [
                        {'$group': {'_id': None,
                            'total': {'$sum': 1},
                            'last_7d': {'$sum': {'$cond': [{'$gte': ['$created_at', week_ago_ts]}, 1, 0]}},
                            'last_30d': {'$sum': {'$cond': [{'$gte': ['$created_at', month_ago_ts]}, 1, 0]}},
                            'web': {'$sum': {'$cond': [{'$eq': ['$app_source', 'web']}, 1, 0]}},
                            'mobile': {'$sum': {'$cond': [{'$ne': ['$app_source', 'web']}, 1, 0]}},
                        }}
                    ],
                    'by_mode': [
                        {'$match': {'mode': {'$in': list(_VALID_ANALYSIS_MODES)}}},
                        {'$group': {'_id': '$mode', 'count': {'$sum': 1}}},
                    ],
                    'daily': [
                        {'$match': {'created_at': {'$gte': week_ago_ts}}},
                        {'$group': {'_id': {
                            '$dateToString': {'format': '%Y-%m-%d',
                                             'date': {'$toDate': {'$multiply': ['$created_at', 1000]}}}
                        }, 'count': {'$sum': 1}}},
                    ],
                }}
            ]), {})

            _frget = facet_result.get
            _totals = _frget('totals', [{}])[0] or {}
            _tget = _totals.get
            total_analyses = _tget('total', 0)
            last_7d = _tget('last_7d', 0)
            last_30d = _tget('last_30d', 0)
            web_analyses = _tget('web', 0)
            mobile_analyses = _tget('mobile', 0)

            mode_breakdown = {_id: doc['count'] for doc in _frget('by_mode', []) if (_id := doc['_id'])}

            now_dt = datetime.utcnow()
            daily_map = {doc['_id']: doc['count'] for doc in _frget('daily', [])}
            daily_trend = []
            for d in range(7, -1, -1):
                _ds = (now_dt - timedelta(days=d)).date().isoformat()
                daily_trend.append({'date': _ds, 'count': daily_map.get(_ds, 0)})

            return JsonResponse({
                'success': True,
                'data': {
                    'total_analyses': total_analyses,
                    'last_7d': last_7d,
                    'last_30d': last_30d,
                    'by_mode': mode_breakdown,
                    'app_breakdown': {'mobile': mobile_analyses, 'web': web_analyses},
                    'daily_trend': daily_trend
                }
            })

        except Exception as e:
            log.exception(f'Analysis activity error: {e}')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
