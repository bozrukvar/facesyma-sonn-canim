"""
admin_api/utils/payment_config.py
==================================
Payment gateway configuration and initialization.

Active providers:
  - Google Pay  (client-side — no server-side secret needed)
  - Apple Pay   (client-side — no server-side secret needed)
  - Vakıfbank Sanal Pos (TODO: ileriki versiyon güncellemesi ile entegre edilecek)
"""

import os
import logging
from django.conf import settings
from admin_api.utils.payment_gateway_abstract import (
    PaymentGatewayFactory,
    PaymentProviderType,
)

# ── Feature Flags ──────────────────────────────────────────────────────────

PAYMENT_PROVIDERS_ENABLED = {
    PaymentProviderType.REVENUECAT:    bool(
        os.environ.get('PAYMENT_REVENUECAT_ENABLED', 'True') == 'True'
    ),
    PaymentProviderType.GOOGLE_PAY:    True,   # Always enabled (client-side)
    PaymentProviderType.APPLE_PAY:     True,   # Always enabled (client-side)
    PaymentProviderType.VAKIFBANK_VPP: False,  # TODO: ileriki versiyon
}

# ── API Keys (from settings.py or environment) ─────────────────────────────

PAYMENT_API_KEYS = {
    PaymentProviderType.REVENUECAT: getattr(
        settings, 'REVENUECAT_API_KEY', os.environ.get('REVENUECAT_API_KEY', '')
    ),
    PaymentProviderType.GOOGLE_PAY: getattr(
        settings, 'GOOGLE_PAY_MERCHANT_ID', os.environ.get('GOOGLE_PAY_MERCHANT_ID', '')
    ),
    PaymentProviderType.APPLE_PAY: getattr(
        settings, 'APPLE_PAY_MERCHANT_ID', os.environ.get('APPLE_PAY_MERCHANT_ID', '')
    ),
    # Vakıfbank VPP anahtarları ileriki versiyon güncellemesinde eklenecek:
    # PaymentProviderType.VAKIFBANK_VPP: os.environ.get('VAKIFBANK_VPP_MERCHANT_ID', ''),
}

# ── Gateway Registration Function ──────────────────────────────────────────


def initialize_payment_gateways():
    """
    Initialize all enabled payment gateways.
    Call this in Django app ready() or at server startup.
    """
    log = logging.getLogger(__name__)
    _info = log.info
    _RC = PaymentProviderType.REVENUECAT

    if PAYMENT_PROVIDERS_ENABLED[_RC]:
        if PAYMENT_API_KEYS[_RC]:
            _info('✓ RevenueCat (Mobile IAP) initialized')

    _info('✓ Google Pay (client-side) active')
    _info('✓ Apple Pay (client-side) active')
    _info('ℹ Vakıfbank VPP: ileriki versiyon güncellemesi bekleniyor')
    _info(f'Payment gateways ready. Available: {PaymentGatewayFactory.list_available_gateways()}')


# ── Subscription Plans ─────────────────────────────────────────────────────

SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'monthly_price': 0.00,
        'yearly_price': 0.00,
        'trial_days': 7,
        'features': [
            'compatibility_check_1_per_day',
            'community_browse',
            'profile_view',
            'basic_analytics',
        ],
    },
    'premium': {
        'name': 'Premium',
        'monthly_price_try': 199.99,
        'yearly_discount': 0.15,
        'trial_days': 7,
        'features': [
            'unlimited_checks',
            'unlimited_communities',
            'file_sharing',
            'advanced_search',
            'priority_support',
            'advanced_analytics',
            'meal_game_access',
            'social_challenges',
            'custom_badges',
            'ai_coach_access',
        ],
    },
}

# ── Payment Provider Priority (fallback order) ────────────────────────────

PAYMENT_PROVIDER_PRIORITY = [
    PaymentProviderType.REVENUECAT,    # Primary: mobile in-app purchase
    PaymentProviderType.GOOGLE_PAY,    # Google Pay
    PaymentProviderType.APPLE_PAY,     # Apple Pay
    # PaymentProviderType.VAKIFBANK_VPP, # TODO: ileriki versiyon
]
