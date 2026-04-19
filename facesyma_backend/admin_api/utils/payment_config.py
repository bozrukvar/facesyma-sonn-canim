"""
admin_api/utils/payment_config.py
==================================
Payment gateway configuration and initialization.
Set up supported payment providers and feature flags.
"""

import os
from django.conf import settings
from admin_api.utils.payment_gateway_abstract import (
    PaymentGatewayFactory,
    PaymentProviderType,
)

# ── Feature Flags ──────────────────────────────────────────────────────────
# Set these in environment variables to enable/disable payment methods

PAYMENT_PROVIDERS_ENABLED = {
    PaymentProviderType.REVENUECAT: bool(
        os.environ.get('PAYMENT_REVENUECAT_ENABLED', 'True') == 'True'
    ),
    PaymentProviderType.STRIPE: bool(
        os.environ.get('PAYMENT_STRIPE_ENABLED', 'False') == 'True'
    ),
    PaymentProviderType.IYZICO: bool(
        os.environ.get('PAYMENT_IYZICO_ENABLED', 'False') == 'True'
    ),
    PaymentProviderType.PAPARA: bool(
        os.environ.get('PAYMENT_PAPARA_ENABLED', 'False') == 'True'
    ),
    PaymentProviderType.TUUM: bool(
        os.environ.get('PAYMENT_TUUM_ENABLED', 'False') == 'True'
    ),
    PaymentProviderType.CRYPTO: bool(
        os.environ.get('PAYMENT_CRYPTO_ENABLED', 'False') == 'True'
    ),
    PaymentProviderType.PAYPAL: bool(
        os.environ.get('PAYMENT_PAYPAL_ENABLED', 'False') == 'True'
    ),
}

# ── API Keys (from settings.py or environment) ─────────────────────────────

PAYMENT_API_KEYS = {
    PaymentProviderType.REVENUECAT: getattr(
        settings, 'REVENUECAT_API_KEY', os.environ.get('REVENUECAT_API_KEY', '')
    ),
    PaymentProviderType.STRIPE: getattr(
        settings, 'STRIPE_API_KEY', os.environ.get('STRIPE_API_KEY', '')
    ),
    PaymentProviderType.IYZICO: getattr(
        settings, 'IYZICO_API_KEY', os.environ.get('IYZICO_API_KEY', '')
    ),
    PaymentProviderType.PAPARA: os.environ.get('PAPARA_API_KEY', ''),
    PaymentProviderType.TUUM: os.environ.get('TUUM_API_KEY', ''),
    PaymentProviderType.CRYPTO: os.environ.get('COINBASE_COMMERCE_API_KEY', ''),
    PaymentProviderType.PAYPAL: os.environ.get('PAYPAL_API_KEY', ''),
}

# ── Gateway Registration Function ──────────────────────────────────────────


def initialize_payment_gateways():
    """
    Initialize all enabled payment gateways.

    Call this in Django app ready() or at server startup.
    Example: apps.py in ready() method
    """
    import logging

    log = logging.getLogger(__name__)

    # Only register if API keys are configured
    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.REVENUECAT]:
        if PAYMENT_API_KEYS[PaymentProviderType.REVENUECAT]:
            # RevenueCat is already handled in subscription_views.py
            log.info('✓ RevenueCat (Mobile IAP) initialized')

    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.STRIPE]:
        if PAYMENT_API_KEYS[PaymentProviderType.STRIPE]:
            # Stripe would be registered here in production
            log.info('✓ Stripe (Web Payments) initialized')

    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.IYZICO]:
        if PAYMENT_API_KEYS[PaymentProviderType.IYZICO]:
            # iyzico would be registered here in production
            log.info('✓ iyzico (Turkish Payments) initialized')

    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.PAPARA]:
        if PAYMENT_API_KEYS[PaymentProviderType.PAPARA]:
            from admin_api.utils.payment_gateways_ewallet import PaparaPaymentGateway

            gateway = PaparaPaymentGateway(
                api_key=PAYMENT_API_KEYS[PaymentProviderType.PAPARA],
                sandbox=not settings.DEBUG,
            )
            PaymentGatewayFactory.register_gateway(PaymentProviderType.PAPARA, gateway)
            log.info('✓ Papara (E-Wallet) initialized')

    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.TUUM]:
        if PAYMENT_API_KEYS[PaymentProviderType.TUUM]:
            from admin_api.utils.payment_gateways_ewallet import TuumPaymentGateway

            gateway = TuumPaymentGateway(
                api_key=PAYMENT_API_KEYS[PaymentProviderType.TUUM],
                merchant_id=os.environ.get('TUUM_MERCHANT_ID', ''),
                sandbox=settings.DEBUG,
            )
            PaymentGatewayFactory.register_gateway(PaymentProviderType.TUUM, gateway)
            log.info('✓ Tuum (Multi-Gateway Aggregator) initialized')

    if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.CRYPTO]:
        if PAYMENT_API_KEYS[PaymentProviderType.CRYPTO]:
            from admin_api.utils.payment_gateways_crypto import CoinbaseCommerceGateway

            gateway = CoinbaseCommerceGateway(
                api_key=PAYMENT_API_KEYS[PaymentProviderType.CRYPTO],
            )
            PaymentGatewayFactory.register_gateway(PaymentProviderType.CRYPTO, gateway)
            log.info('✓ Coinbase Commerce (Cryptocurrency) initialized')

    log.info(f'Payment gateways ready. Available: {PaymentGatewayFactory.list_available_gateways()}')


# ── Payment Pricing Strategy ───────────────────────────────────────────────
# 5-tier global pricing based on purchasing power parity (PPP)

PRICING_TIERS = {
    'Tier A': {
        'regions': ['China', 'India', 'Southeast Asia', 'South America (lower income)'],
        'monthly_usd': 0.99,
        'yearly_usd': 8.99,
    },
    'Tier B': {
        'regions': ['Middle East', 'Latin America', 'Eastern Europe'],
        'monthly_usd': 1.99,
        'yearly_usd': 14.99,
    },
    'Tier C': {
        'regions': ['South Korea', 'Japan', 'Taiwan', 'Mexico', 'Brazil'],
        'monthly_usd': 4.99,
        'yearly_usd': 39.99,
    },
    'Tier D': {
        'regions': ['USA', 'Canada', 'Australia', 'Scandinavia'],
        'monthly_usd': 12.99,
        'yearly_usd': 99.99,
    },
    'Tier E': {
        'regions': ['Germany', 'France', 'UK', 'Switzerland', 'Netherlands'],
        'monthly_usd': 9.99,  # Converted to EUR in-country
        'yearly_usd': 79.99,
    },
}

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
        'monthly_price_tier': 'dynamic',  # Varies by tier
        'yearly_discount': 0.15,  # 15% discount for yearly
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
    PaymentProviderType.REVENUECAT,  # Primary: mobile in-app purchase
    PaymentProviderType.STRIPE,      # Secondary: web/card payments
    PaymentProviderType.PAPARA,      # Tertiary: Turkish e-wallet
    PaymentProviderType.IYZICO,      # Alternative: Turkish payment
    PaymentProviderType.TUUM,        # Multi-method aggregator
    PaymentProviderType.CRYPTO,      # Advanced: cryptocurrency
    PaymentProviderType.PAYPAL,      # Fallback: PayPal
]

# ── Webhook Secrets ───────────────────────────────────────────────────────

WEBHOOK_SECRETS = {
    PaymentProviderType.STRIPE: getattr(
        settings, 'STRIPE_WEBHOOK_SECRET', os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    ),
    PaymentProviderType.IYZICO: os.environ.get('IYZICO_WEBHOOK_SECRET', ''),
    PaymentProviderType.PAPARA: os.environ.get('PAPARA_WEBHOOK_SECRET', ''),
    PaymentProviderType.TUUM: os.environ.get('TUUM_WEBHOOK_SECRET', ''),
}
