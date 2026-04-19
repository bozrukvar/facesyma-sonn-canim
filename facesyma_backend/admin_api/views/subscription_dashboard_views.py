"""
admin_api/views/subscription_dashboard_views.py
================================================
Subscription dashboard and management views for admin panel.
Real-time metrics, user lookup, and subscription management.
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
    """MongoDB connection"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


# ══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION METRICS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionMetricsView(View):
    """
    Real-time subscription metrics dashboard.
    Shows MRR, active subscriptions, churn rate, etc.
    """

    def get(self, request):
        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            now = datetime.now().isoformat()

            # Active subscriptions
            active_count = subscriptions.count_documents({
                'plan': 'premium',
                'expires_date': {'$gt': now}
            })

            # Cancelled last 30 days
            cancelled_30d = subscriptions.count_documents({
                'cancelled_at': {
                    '$exists': True,
                    '$gte': (datetime.now() - timedelta(days=30)).isoformat()
                }
            })

            # Calculate MRR (estimate from active subscriptions)
            by_tier = list(subscriptions.aggregate([
                {
                    '$match': {
                        'plan': 'premium',
                        'expires_date': {'$gt': now}
                    }
                },
                {
                    '$group': {
                        '_id': '$tier',
                        'count': {'$sum': 1},
                        'avg_price': {'$avg': '$monthly_price'}
                    }
                }
            ]))

            # Estimate MRR
            mrr = sum(tier.get('count', 0) * tier.get('avg_price', 0) for tier in by_tier) if by_tier else 0

            # Churn rate
            churn_rate = (cancelled_30d / active_count * 100) if active_count > 0 else 0

            # New subscriptions (last 7 days)
            new_7d = subscriptions.count_documents({
                'verified_at': {
                    '$gte': (datetime.now() - timedelta(days=7)).isoformat()
                }
            })

            # Conversion rate (trial to paid - estimated)
            # This would need additional tracking in real implementation
            conversion_rate = 18.5  # Placeholder - should come from payment_transactions

            return JsonResponse({
                'metrics': {
                    'active_subscriptions': active_count,
                    'mrr': round(mrr, 2),
                    'arr': round(mrr * 12, 2),
                    'churn_rate_30d': round(churn_rate, 1),
                    'new_subscriptions_7d': new_7d,
                    'conversion_rate': conversion_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'by_tier': [
                    {
                        'tier': tier.get('_id', 'unknown'),
                        'count': tier.get('count', 0),
                        'estimated_mrr': round(tier.get('count', 0) * tier.get('avg_price', 0), 2)
                    }
                    for tier in by_tier
                ]
            })

        except Exception as e:
            log.exception(f'Subscription metrics error: {e}')
            return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
# USER SUBSCRIPTION LOOKUP & MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserSubscriptionDetailView(View):
    """
    Get detailed subscription info for a user.
    Admin can view and manage subscription.
    """

    def get(self, request, user_id):
        """Get user subscription details"""
        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            # Get user info
            user = users.find_one({'id': int(user_id)})
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            # Get subscription
            sub = subscriptions.find_one({'user_id': int(user_id)})

            if not sub:
                # Return default free subscription
                return JsonResponse({
                    'user': {
                        'id': user['id'],
                        'email': user.get('email', ''),
                        'username': user.get('username', ''),
                        'date_joined': user.get('date_joined', '')
                    },
                    'subscription': {
                        'plan': 'free',
                        'active': False,
                        'provider': None,
                        'expires_date': None,
                        'verified_at': None,
                        'entitlements': []
                    }
                })

            return JsonResponse({
                'user': {
                    'id': user['id'],
                    'email': user.get('email', ''),
                    'username': user.get('username', ''),
                    'date_joined': user.get('date_joined', '')
                },
                'subscription': {
                    'plan': sub.get('plan', 'free'),
                    'active': sub.get('plan') == 'premium',
                    'provider': sub.get('provider', ''),
                    'tier': sub.get('tier', ''),
                    'expires_date': sub.get('expires_date'),
                    'verified_at': sub.get('verified_at'),
                    'cancelled_at': sub.get('cancelled_at'),
                    'entitlements': list(sub.get('entitlements', {}).keys()),
                    'original_purchase_date': sub.get('original_purchase_date'),
                    'monthly_price': sub.get('monthly_price'),
                    'billing_currency': sub.get('billing_currency')
                }
            })

        except Exception as e:
            log.exception(f'User subscription lookup error: {e}')
            return JsonResponse({'error': str(e)}, status=500)

    def post(self, request, user_id):
        """Update user subscription (admin override)"""
        try:
            data = json.loads(request.body)
            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            action = data.get('action')
            user_id = int(user_id)

            if action == 'grant_premium':
                # Grant premium access
                tier = data.get('tier', 'tier_d')
                days = data.get('days', 30)

                expires = (datetime.now() + timedelta(days=days)).isoformat()

                subscriptions.update_one(
                    {'user_id': user_id},
                    {
                        '$set': {
                            'plan': 'premium',
                            'tier': tier,
                            'provider': 'admin_grant',
                            'expires_date': expires,
                            'verified_at': datetime.now().isoformat(),
                            'entitlements': {'premium': True}
                        }
                    },
                    upsert=True
                )

                users.update_one(
                    {'id': user_id},
                    {'$set': {'plan': 'premium'}}
                )

                log.info(f"✅ Admin granted premium to user {user_id} for {days} days")

                return JsonResponse({
                    'success': True,
                    'message': f'Premium granted for {days} days',
                    'expires': expires
                })

            elif action == 'downgrade_to_free':
                # Downgrade to free
                subscriptions.update_one(
                    {'user_id': user_id},
                    {
                        '$set': {
                            'plan': 'free',
                            'cancelled_at': datetime.now().isoformat()
                        }
                    }
                )

                users.update_one(
                    {'id': user_id},
                    {'$set': {'plan': 'free'}}
                )

                log.info(f"✅ Admin downgraded user {user_id} to free")

                return JsonResponse({
                    'success': True,
                    'message': 'User downgraded to free plan'
                })

            elif action == 'issue_refund':
                # Record refund
                amount = data.get('amount', 0)
                reason = data.get('reason', 'Admin refund')

                db['payment_transactions'].insert_one({
                    'user_id': user_id,
                    'provider': 'admin_refund',
                    'amount': -amount,
                    'status': 'refunded',
                    'reason': reason,
                    'created_at': datetime.now().isoformat()
                })

                log.info(f"✅ Admin refund issued to user {user_id}: ${amount}")

                return JsonResponse({
                    'success': True,
                    'message': f'Refund of ${amount} recorded'
                })

            else:
                return JsonResponse({'error': 'Unknown action'}, status=400)

        except Exception as e:
            log.exception(f'Subscription update error: {e}')
            return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionSearchView(View):
    """Search users by subscription status or email"""

    def get(self, request):
        try:
            query = request.GET.get('q', '').strip()
            status = request.GET.get('status', 'all')  # all, premium, free
            limit = int(request.GET.get('limit', 50))

            if not query and status == 'all':
                return JsonResponse({'error': 'Provide search query or status filter'}, status=400)

            db = _get_db()
            subscriptions = db['user_subscriptions']
            users = db['appfaceapi_myuser']

            # Build MongoDB query
            mongo_query = {}

            if status != 'all':
                mongo_query['plan'] = status

            if query:
                # Search by email or username
                user_list = list(users.find(
                    {
                        '$or': [
                            {'email': {'$regex': query, '$options': 'i'}},
                            {'username': {'$regex': query, '$options': 'i'}}
                        ]
                    },
                    {'_id': 0, 'id': 1}
                ).limit(limit))

                if not user_list:
                    return JsonResponse({'results': []})

                user_ids = [u['id'] for u in user_list]
                mongo_query['user_id'] = {'$in': user_ids}

            # Find subscriptions
            results = list(subscriptions.find(mongo_query).limit(limit))

            # Enrich with user info
            enriched = []
            for sub in results:
                user = users.find_one({'id': sub['user_id']})
                enriched.append({
                    'user_id': sub['user_id'],
                    'email': user.get('email', '') if user else '',
                    'username': user.get('username', '') if user else '',
                    'plan': sub.get('plan', 'free'),
                    'tier': sub.get('tier', ''),
                    'expires_date': sub.get('expires_date'),
                    'verified_at': sub.get('verified_at')
                })

            return JsonResponse({
                'count': len(enriched),
                'results': enriched
            })

        except Exception as e:
            log.exception(f'Subscription search error: {e}')
            return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
# CHURN ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChurnAnalysisView(View):
    """Analyze churn patterns and at-risk users"""

    def get(self, request):
        try:
            db = _get_db()
            subscriptions = db['user_subscriptions']
            now = datetime.now()

            # Calculate churn for different periods
            churn_data = {}
            for days in [7, 30, 90]:
                period_start = (now - timedelta(days=days)).isoformat()
                cancelled = subscriptions.count_documents({
                    'cancelled_at': {'$gte': period_start}
                })
                churn_data[f'churn_{days}d'] = cancelled

            # At-risk users (expiring soon - within 7 days)
            expiring_soon = (now + timedelta(days=7)).isoformat()
            at_risk = list(subscriptions.find(
                {
                    'plan': 'premium',
                    'expires_date': {'$lt': expiring_soon, '$gt': now.isoformat()}
                },
                {'_id': 0, 'user_id': 1, 'expires_date': 1, 'tier': 1}
            ).limit(50))

            return JsonResponse({
                'churn': churn_data,
                'at_risk_count': len(at_risk),
                'at_risk_users': at_risk
            })

        except Exception as e:
            log.exception(f'Churn analysis error: {e}')
            return JsonResponse({'error': str(e)}, status=500)
