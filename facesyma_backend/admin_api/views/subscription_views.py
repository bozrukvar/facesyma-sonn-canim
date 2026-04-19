"""
admin_api/views/subscription_views.py
=====================================
Mobile In-App Purchase Verification (RevenueCat)
- Verify App Store receipts
- Verify Google Play receipts
- Sync subscription status to backend
- Feature access control
"""

import json
import requests
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from pymongo import MongoClient
from django.conf import settings

import logging
log = logging.getLogger(__name__)

# ── RevenueCat API Configuration ────────────────────────────────────────────
REVENUECAT_API_KEY = getattr(settings, 'REVENUECAT_API_KEY', 'sk_test_xxxxx')
REVENUECAT_BASE_URL = 'https://api.revenuecat.com/v1'


def _get_db():
    """MongoDB bağlantısı"""
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client['facesyma-backend']


def _verify_receipt_with_revenuecat(receipt, is_ios=True):
    """
    Verify receipt with RevenueCat API
    RevenueCat handles App Store & Google Play verification
    """
    try:
        headers = {
            'Authorization': f'Bearer {REVENUECAT_API_KEY}',
            'Content-Type': 'application/json',
        }

        # RevenueCat customer endpoint
        url = f'{REVENUECAT_BASE_URL}/receipts'

        payload = {
            'app_user_id': receipt.get('user_id'),
            'fetch_token': receipt.get('fetch_token'),  # RevenueCat subscription token
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        return response.json()
    except Exception as e:
        log.error(f'RevenueCat verification error: {e}')
        return None


# ── Verify Subscription ─────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class VerifySubscriptionView(View):
    """
    Mobile app calls this to verify subscription status
    After user purchases via App Store/Play Store
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            fetch_token = data.get('fetch_token')  # RevenueCat token
            is_ios = data.get('is_ios', True)

            if not user_id or not fetch_token:
                return JsonResponse(
                    {'detail': 'user_id ve fetch_token zorunlu.'},
                    status=400
                )

            # Verify with RevenueCat
            rc_response = _verify_receipt_with_revenuecat(
                {'user_id': user_id, 'fetch_token': fetch_token},
                is_ios=is_ios
            )

            if not rc_response:
                return JsonResponse(
                    {'detail': 'Receipt verification failed'},
                    status=401
                )

            # Extract subscription info
            subscriber = rc_response.get('subscriber', {})
            entitlements = subscriber.get('entitlements', {})
            active_subscriptions = subscriber.get('subscriptions', {})

            # Determine plan
            plan = 'free'
            if active_subscriptions:
                plan = 'premium'

            # Update MongoDB
            db = _get_db()
            users_col = db['appfaceapi_myuser']
            subscriptions_col = db['user_subscriptions']

            # Update user plan
            users_col.update_one(
                {'id': user_id},
                {
                    '$set': {
                        'plan': plan,
                        'updated_at': datetime.now().isoformat(),
                    }
                }
            )

            # Store subscription details
            subscription_doc = {
                'user_id': user_id,
                'plan': plan,
                'provider': 'revenuecat',
                'entitlements': entitlements,
                'subscriptions': active_subscriptions,
                'original_purchase_date': subscriber.get('original_purchase_date'),
                'expires_date': subscriber.get('expires_date'),
                'verified_at': datetime.now().isoformat(),
            }

            subscriptions_col.update_one(
                {'user_id': user_id},
                {'$set': subscription_doc},
                upsert=True
            )

            return JsonResponse({
                'success': True,
                'plan': plan,
                'entitlements': list(entitlements.keys()),
                'expires_date': subscriber.get('expires_date'),
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except Exception as e:
            log.exception(f'Subscription verification error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Get Subscription Status ─────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionStatusView(View):
    """Get user's current subscription status"""

    def get(self, request, user_id):
        try:
            db = _get_db()
            subscriptions_col = db['user_subscriptions']

            sub = subscriptions_col.find_one({'user_id': int(user_id)})

            if not sub:
                return JsonResponse({
                    'plan': 'free',
                    'active': False,
                    'entitlements': [],
                })

            return JsonResponse({
                'plan': sub.get('plan', 'free'),
                'active': sub.get('plan') == 'premium',
                'entitlements': list(sub.get('entitlements', {}).keys()),
                'expires_date': sub.get('expires_date'),
                'verified_at': sub.get('verified_at'),
            })

        except Exception as e:
            log.exception(f'Error getting subscription status: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Check Feature Access ────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class FeatureAccessView(View):
    """
    Check if user has access to premium feature
    Called before showing paywall
    """

    def get(self, request, user_id):
        try:
            feature = request.GET.get('feature', '')
            if not feature:
                return JsonResponse({'detail': 'feature parameter required'}, status=400)

            db = _get_db()
            users_col = db['appfaceapi_myuser']

            user = users_col.find_one({'id': int(user_id)})
            if not user:
                return JsonResponse({'detail': 'User not found'}, status=404)

            plan = user.get('plan', 'free')

            # Feature matrix
            free_features = [
                'compatibility_check_1_per_day',
                'community_browse',
                'profile_view',
            ]

            premium_features = free_features + [
                'unlimited_checks',
                'unlimited_communities',
                'file_sharing',
                'advanced_search',
                'priority_support',
            ]

            if plan == 'premium':
                has_access = feature in premium_features
            else:
                has_access = feature in free_features

            return JsonResponse({
                'feature': feature,
                'has_access': has_access,
                'plan': plan,
                'upgrade_required': not has_access,
            })

        except Exception as e:
            log.exception(f'Feature access check error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)


# ── Cancel Subscription ─────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CancelSubscriptionView(View):
    """Cancel/refund subscription (user initiates in app)"""

    def post(self, request, user_id):
        try:
            db = _get_db()
            subscriptions_col = db['user_subscriptions']
            users_col = db['appfaceapi_myuser']

            # Mark subscription as cancelled
            subscriptions_col.update_one(
                {'user_id': int(user_id)},
                {
                    '$set': {
                        'plan': 'free',
                        'cancelled_at': datetime.now().isoformat(),
                    }
                }
            )

            # Update user plan
            users_col.update_one(
                {'id': int(user_id)},
                {'$set': {'plan': 'free'}}
            )

            return JsonResponse({
                'success': True,
                'message': 'Subscription cancelled',
                'plan': 'free',
            })

        except Exception as e:
            log.exception(f'Cancellation error: {e}')
            return JsonResponse({'detail': str(e)}, status=500)
