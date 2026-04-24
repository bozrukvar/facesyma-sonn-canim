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
import jwt
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from admin_api.utils.mongo import _get_db
from django.conf import settings

import logging
log = logging.getLogger(__name__)

_JWT_SECRET: str  = settings.JWT_SECRET
_SUB_DETAIL_PROJ  = {'_id': 0, 'plan': 1, 'entitlements': 1, 'expires_date': 1, 'verified_at': 1}

_FREE_FEATURES = frozenset([
    'compatibility_check_1_per_day',
    'community_browse',
    'profile_view',
])
_PREMIUM_FEATURES = _FREE_FEATURES | frozenset([
    'unlimited_checks',
    'unlimited_communities',
    'file_sharing',
    'advanced_search',
    'priority_support',
])


def _get_user_id(request):
    """Extract user_id from JWT Bearer token."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = jwt.decode(
            auth.split(' ', 1)[1], _JWT_SECRET, algorithms=['HS256']
        )
        return payload.get('user_id')
    except Exception:
        return None

# ── RevenueCat API Configuration ────────────────────────────────────────────
REVENUECAT_API_KEY = getattr(settings, 'REVENUECAT_API_KEY', 'sk_test_xxxxx')
REVENUECAT_BASE_URL = 'https://api.revenuecat.com/v1'





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

        _rget = receipt.get
        payload = {
            'app_user_id': _rget('user_id'),
            'fetch_token': _rget('fetch_token'),  # RevenueCat subscription token
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
            user_id = _get_user_id(request)
            if not user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            data = json.loads(request.body)
            _dget = data.get
            fetch_token = _dget('fetch_token')  # RevenueCat token
            is_ios = _dget('is_ios', True)

            if not fetch_token:
                return JsonResponse(
                    {'detail': 'fetch_token zorunlu.'},
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
            _subget = subscriber.get
            entitlements = _subget('entitlements', {})
            active_subscriptions = _subget('subscriptions', {})

            # Determine plan
            plan = 'free'
            if active_subscriptions:
                plan = 'premium'

            # Update MongoDB
            _now = datetime.utcnow()
            _now_iso = _now.isoformat()
            db = _get_db()
            users_col = db['appfaceapi_myuser']
            subscriptions_col = db['user_subscriptions']

            # Update user plan
            users_col.update_one(
                {'id': user_id},
                {
                    '$set': {
                        'plan': plan,
                        'updated_at': _now_iso,
                    }
                }
            )

            # Store subscription details
            _expires_date = _subget('expires_date')
            subscription_doc = {
                'user_id': user_id,
                'plan': plan,
                'provider': 'revenuecat',
                'entitlements': entitlements,
                'subscriptions': active_subscriptions,
                'original_purchase_date': _subget('original_purchase_date'),
                'expires_date': _expires_date,
                'verified_at': _now_iso,
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
                'expires_date': _expires_date,
            })

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except Exception as e:
            log.exception('Subscription verification error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Get Subscription Status ─────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionStatusView(View):
    """Get user's current subscription status"""

    def get(self, request, user_id):
        try:
            token_user_id = _get_user_id(request)
            if not token_user_id or token_user_id != user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            db = _get_db()
            subscriptions_col = db['user_subscriptions']

            sub = subscriptions_col.find_one({'user_id': user_id}, _SUB_DETAIL_PROJ)

            if not sub:
                return JsonResponse({
                    'plan': 'free',
                    'active': False,
                    'entitlements': [],
                })

            _sget2 = sub.get
            _plan = _sget2('plan', 'free')
            return JsonResponse({
                'plan': _plan,
                'active': _plan == 'premium',
                'entitlements': list(_sget2('entitlements', {}).keys()),
                'expires_date': _sget2('expires_date'),
                'verified_at': _sget2('verified_at'),
            })

        except Exception as e:
            log.exception('Error getting subscription status')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Check Feature Access ────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class FeatureAccessView(View):
    """
    Check if user has access to premium feature
    Called before showing paywall
    """

    def get(self, request, user_id):
        try:
            token_user_id = _get_user_id(request)
            if not token_user_id or token_user_id != user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            feature = request.GET.get('feature', '')
            if not feature:
                return JsonResponse({'detail': 'feature parameter required'}, status=400)

            db = _get_db()
            users_col = db['appfaceapi_myuser']

            user = users_col.find_one({'id': user_id}, {'_id': 0, 'plan': 1})
            if not user:
                return JsonResponse({'detail': 'User not found'}, status=404)

            plan = user.get('plan', 'free')

            if plan == 'premium':
                has_access = feature in _PREMIUM_FEATURES
            else:
                has_access = feature in _FREE_FEATURES

            return JsonResponse({
                'feature': feature,
                'has_access': has_access,
                'plan': plan,
                'upgrade_required': not has_access,
            })

        except Exception as e:
            log.exception('Feature access check error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)


# ── Cancel Subscription ─────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class CancelSubscriptionView(View):
    """Cancel/refund subscription (user initiates in app)"""

    def post(self, request, user_id):
        try:
            token_user_id = _get_user_id(request)
            if not token_user_id or token_user_id != user_id:
                return JsonResponse({'detail': 'Authentication required.'}, status=401)

            db = _get_db()
            subscriptions_col = db['user_subscriptions']
            users_col = db['appfaceapi_myuser']

            # Mark subscription as cancelled
            subscriptions_col.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'plan': 'free',
                        'cancelled_at': datetime.utcnow().isoformat(),
                    }
                }
            )

            # Update user plan
            users_col.update_one(
                {'id': user_id},
                {'$set': {'plan': 'free'}}
            )

            return JsonResponse({
                'success': True,
                'message': 'Subscription cancelled',
                'plan': 'free',
            })

        except Exception as e:
            log.exception('Cancellation error')
            return JsonResponse({'detail': 'Internal server error.'}, status=500)
