"""
admin_api/views/subscription_dashboard_views.py
================================================
Subscription dashboard and management views for admin panel.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from admin_api.utils.auth import _require_admin

log = logging.getLogger(__name__)

_VALID_SUB_ACTIONS = frozenset({'grant_premium', 'downgrade_to_free', 'issue_refund'})
_SUB_DETAIL_PROJ = {
    '_id': 0, 'plan': 1, 'active': 1, 'provider': 1, 'tier': 1,
    'expires_date': 1, 'verified_at': 1, 'cancelled_at': 1, 'entitlements': 1,
    'original_purchase_date': 1, 'monthly_price': 1, 'billing_currency': 1,
}
_SUB_LIST_PROJ    = {'_id': 0, 'user_id': 1, 'plan': 1, 'tier': 1, 'expires_date': 1, 'verified_at': 1}
_SUB_USER_PROJ    = {'id': 1, 'email': 1, 'username': 1}
_SUB_USER_ID_PROJ = {'_id': 0, 'id': 1, 'email': 1, 'username': 1, 'date_joined': 1}
_SUB_ATRISK_PROJ  = {'_id': 0, 'user_id': 1, 'expires_date': 1, 'tier': 1}


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionMetricsView(View):
    """Real-time subscription metrics dashboard."""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            _now = datetime.utcnow()
            now   = _now.isoformat()
            ago30 = (_now - timedelta(days=30)).isoformat()
            ago7  = (_now - timedelta(days=7)).isoformat()
            _sm = next(subscriptions.aggregate([{'$facet': {
                'active':   [{'$match': {'plan': 'premium', 'expires_date': {'$gt': now}}}, {'$count': 'n'}],
                'cancel30': [{'$match': {'cancelled_at': {'$exists': True, '$gte': ago30}}}, {'$count': 'n'}],
                'new7d':    [{'$match': {'verified_at': {'$gte': ago7}}}, {'$count': 'n'}],
                'by_tier':  [
                    {'$match': {'plan': 'premium', 'expires_date': {'$gt': now}}},
                    {'$group': {'_id': '$tier', 'count': {'$sum': 1}, 'avg_price': {'$avg': '$monthly_price'}}},
                ],
            }}]), {})
            _smget = _sm.get
            active_count  = (_smget('active',   [{}])[0] or {}).get('n', 0)
            cancelled_30d = (_smget('cancel30', [{}])[0] or {}).get('n', 0)
            new_7d        = (_smget('new7d',    [{}])[0] or {}).get('n', 0)
            by_tier       = _smget('by_tier', [])

            mrr = sum((_tg := tier.get)('count', 0) * _tg('avg_price', 0) for tier in by_tier) if by_tier else 0
            churn_rate = (cancelled_30d / active_count * 100) if active_count > 0 else 0

            return JsonResponse({
                'metrics': {
                    'active_subscriptions': active_count,
                    'mrr': round(mrr, 2),
                    'arr': round(mrr * 12, 2),
                    'churn_rate_30d': round(churn_rate, 1),
                    'new_subscriptions_7d': new_7d,
                    'timestamp': now
                },
                'by_tier': [
                    {
                        'tier': (_tg := tier.get)('_id', 'unknown'),
                        'count': (_tc := _tg('count', 0)),
                        'estimated_mrr': round(_tc * _tg('avg_price', 0), 2)
                    }
                    for tier in by_tier
                ]
            })

        except Exception as e:
            log.exception(f'Subscription metrics error: {e}')
            return JsonResponse({'error': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserSubscriptionDetailView(View):
    """Get and manage subscription for a specific user."""

    def get(self, request, user_id):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            try:
                uid = int(user_id)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Invalid user_id'}, status=400)

            user = users.find_one({'id': uid}, _SUB_USER_ID_PROJ)
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            sub = subscriptions.find_one({'user_id': uid}, _SUB_DETAIL_PROJ)

            _uget = user.get
            user_data = {
                'id': user['id'],
                'email': _uget('email', ''),
                'username': _uget('username', ''),
                'date_joined': _uget('date_joined', '')
            }

            if not sub:
                return JsonResponse({
                    'user': user_data,
                    'subscription': {'plan': 'free', 'active': False, 'provider': None, 'expires_date': None, 'verified_at': None, 'entitlements': []}
                })

            _subget = sub.get
            _plan = _subget('plan', 'free')
            return JsonResponse({
                'user': user_data,
                'subscription': {
                    'plan': _plan,
                    'active': _plan == 'premium',
                    'provider': _subget('provider', ''),
                    'tier': _subget('tier', ''),
                    'expires_date': _subget('expires_date'),
                    'verified_at': _subget('verified_at'),
                    'cancelled_at': _subget('cancelled_at'),
                    'entitlements': list(_subget('entitlements', {}).keys()),
                    'original_purchase_date': _subget('original_purchase_date'),
                    'monthly_price': _subget('monthly_price'),
                    'billing_currency': _subget('billing_currency')
                }
            })

        except Exception as e:
            log.exception(f'User subscription lookup error: {e}')
            return JsonResponse({'error': 'Internal server error.'}, status=500)

    def post(self, request, user_id):
        try:
            admin_payload = _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            data = json.loads(request.body)
            _admin_email = admin_payload.get('email', 'admin')
            _now = datetime.utcnow()
            _now_iso = _now.isoformat()
            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            try:
                uid = int(user_id)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Invalid user_id'}, status=400)

            _dget = data.get
            _li   = log.info
            action = _dget('action')
            if action not in _VALID_SUB_ACTIONS:
                return JsonResponse({'error': f'Unknown action. Allowed: {", ".join(sorted(_VALID_SUB_ACTIONS))}'}, status=400)

            if action == 'grant_premium':
                tier = _dget('tier', 'tier_d')
                if tier not in ('tier_a', 'tier_b', 'tier_c', 'tier_d'):
                    return JsonResponse({'error': 'Invalid tier. Allowed: tier_a, tier_b, tier_c, tier_d'}, status=400)
                try:
                    days = min(max(1, int(_dget('days', 30))), 365)
                except (TypeError, ValueError):
                    days = 30

                expires = (_now + timedelta(days=days)).isoformat()

                subscriptions.update_one(
                    {'user_id': uid},
                    {'$set': {'plan': 'premium', 'tier': tier, 'provider': 'admin_grant', 'expires_date': expires, 'verified_at': _now_iso, 'entitlements': {'premium': True}, 'granted_by': _admin_email}},
                    upsert=True
                )
                users.update_one({'id': uid}, {'$set': {'plan': 'premium'}})
                _li(f"Admin {_admin_email} granted premium to user {uid} for {days} days")

                return JsonResponse({'success': True, 'message': f'Premium granted for {days} days', 'expires': expires})

            elif action == 'downgrade_to_free':
                subscriptions.update_one(
                    {'user_id': uid},
                    {'$set': {'plan': 'free', 'cancelled_at': _now_iso, 'cancelled_by': _admin_email}}
                )
                users.update_one({'id': uid}, {'$set': {'plan': 'free'}})
                _li(f"Admin {_admin_email} downgraded user {uid} to free")

                return JsonResponse({'success': True, 'message': 'User downgraded to free plan'})

            elif action == 'issue_refund':
                try:
                    amount = float(_dget('amount', 0))
                except (TypeError, ValueError):
                    amount = 0.0
                reason = str(_dget('reason', 'Admin refund'))[:500]

                db['payment_transactions'].insert_one({
                    'user_id': uid,
                    'provider': 'admin_refund',
                    'amount': -amount,
                    'status': 'refunded',
                    'reason': reason,
                    'issued_by': _admin_email,
                    'created_at': _now_iso
                })
                _li(f"Admin {_admin_email} issued refund to user {uid}: ${amount}")

                return JsonResponse({'success': True, 'message': f'Refund of ${amount} recorded'})

        except Exception as e:
            log.exception(f'Subscription update error: {e}')
            return JsonResponse({'error': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionSearchView(View):
    """Search users by subscription status or email."""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            _qp = request.GET
            _qpget = _qp.get
            query = _qpget('q', '').strip()[:100]
            status = _qpget('status', 'all')
            if status not in ('all', 'premium', 'free'):
                status = 'all'
            try:
                limit = min(max(1, int(_qpget('limit', 50))), 200)
            except (ValueError, TypeError):
                limit = 50

            if not query and status == 'all':
                return JsonResponse({'error': 'Provide search query or status filter'}, status=400)

            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            mongo_query = {}
            if status != 'all':
                mongo_query['plan'] = status

            if query:
                safe_query = re.escape(query)
                user_list = list(users.find(
                    {'$or': [
                        {'email': {'$regex': safe_query, '$options': 'i'}},
                        {'username': {'$regex': safe_query, '$options': 'i'}}
                    ]},
                    {'_id': 0, 'id': 1}
                ).limit(limit))

                if not user_list:
                    return JsonResponse({'results': []})

                user_ids = [u['id'] for u in user_list]
                mongo_query['user_id'] = {'$in': user_ids}

            results = list(subscriptions.find(mongo_query, _SUB_LIST_PROJ).limit(limit))

            sub_user_ids = [s['user_id'] for s in results]
            users_map = {u['id']: u for u in users.find(
                {'id': {'$in': sub_user_ids}}, _SUB_USER_PROJ
            )}
            enriched = []
            for sub in results:
                _uid = sub['user_id']
                user = users_map.get(_uid)
                _s2get = sub.get
                enriched.append({
                    'user_id': _uid,
                    'email': user.get('email', '') if user else '',
                    'username': user.get('username', '') if user else '',
                    'plan': _s2get('plan', 'free'),
                    'tier': _s2get('tier', ''),
                    'expires_date': _s2get('expires_date'),
                    'verified_at': _s2get('verified_at')
                })

            return JsonResponse({'count': len(enriched), 'results': enriched})

        except Exception as e:
            log.exception(f'Subscription search error: {e}')
            return JsonResponse({'error': 'Internal server error.'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ChurnAnalysisView(View):
    """Analyze churn patterns and at-risk users."""

    def get(self, request):
        try:
            _require_admin(request)
        except ValueError as e:
            return JsonResponse({'detail': str(e)}, status=401)
        except PermissionError as e:
            return JsonResponse({'detail': str(e)}, status=403)

        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            now = datetime.utcnow()

            p7  = (now - timedelta(days=7)).isoformat()
            p30 = (now - timedelta(days=30)).isoformat()
            p90 = (now - timedelta(days=90)).isoformat()
            _churn = next(subscriptions.aggregate([{'$group': {'_id': None,
                'churn_7d':  {'$sum': {'$cond': [{'$gte': ['$cancelled_at', p7]},  1, 0]}},
                'churn_30d': {'$sum': {'$cond': [{'$gte': ['$cancelled_at', p30]}, 1, 0]}},
                'churn_90d': {'$sum': {'$cond': [{'$gte': ['$cancelled_at', p90]}, 1, 0]}},
            }}]), {'churn_7d': 0, 'churn_30d': 0, 'churn_90d': 0})
            churn_data = {
                'churn_7d':  _churn['churn_7d'],
                'churn_30d': _churn['churn_30d'],
                'churn_90d': _churn['churn_90d'],
            }

            expiring_soon = (now + timedelta(days=7)).isoformat()
            at_risk = list(subscriptions.find(
                {'plan': 'premium', 'expires_date': {'$lt': expiring_soon, '$gt': now.isoformat()}},
                _SUB_ATRISK_PROJ
            ).limit(50))

            return JsonResponse({
                'churn': churn_data,
                'at_risk_count': len(at_risk),
                'at_risk_users': at_risk
            })

        except Exception as e:
            log.exception(f'Churn analysis error: {e}')
            return JsonResponse({'error': 'Internal server error.'}, status=500)
