# Facesyma Payment Architecture

## Overview

Facesyma uses a **multi-provider payment gateway architecture** to support diverse payment methods globally:

1. **RevenueCat** (Primary) - Mobile In-App Purchases (iOS App Store, Android Google Play)
2. **Stripe** - Card payments, digital wallets (web)
3. **iyzico** - Turkish local payments
4. **Papara** - Turkish e-wallet
5. **Tuum** - Multi-provider aggregator (150+ methods)
6. **Cryptocurrency** - Bitcoin, Ethereum, USDC via Coinbase Commerce
7. **PayPal** - Global fallback payment method

## Architecture

### 1. Payment Gateway Abstraction Layer

**File:** `admin_api/utils/payment_gateway_abstract.py`

Provides abstract base classes for all payment providers:

```python
class BasePaymentGateway(ABC):
    """All payment gateways must implement these methods"""
    async def process_payment(...)      # Charge user
    async def refund_payment(...)       # Issue refund
    async def verify_payment(...)       # Verify receipt
    async def get_subscription_status(...) # Check subscription
    async def cancel_subscription(...)  # Cancel subscription
    async def health_check()            # Check API connectivity
```

### 2. Provider Implementations

#### Mobile In-App Purchase (RevenueCat)
- **File:** `admin_api/views/subscription_views.py`
- **Status:** ✅ FULLY IMPLEMENTED
- **Endpoints:**
  - `POST /api/subscription/verify/` - Verify App Store/Play Store receipts
  - `GET /api/subscription/status/<user_id>/` - Get subscription status
  - `GET /api/subscription/feature/<user_id>/` - Check feature access
  - `POST /api/subscription/cancel/<user_id>/` - Cancel subscription

**Why RevenueCat?**
- Handles iOS App Store + Android Google Play automatically
- 150+ countries with pre-configured regional pricing
- Automatic currency conversion
- Receipt verification built-in
- No backend payment processing needed for mobile

#### E-Wallet Integrations (Future)
- **File:** `admin_api/utils/payment_gateways_ewallet.py`
- **Status:** 🔲 SKELETON (ready to implement)
- **Providers:**
  - **Papara** - Turkish e-wallet platform
  - **Tuum** - Multi-provider aggregator (supports 150+ payment methods)

#### Cryptocurrency (Future)
- **File:** `admin_api/utils/payment_gateways_crypto.py`
- **Status:** 🔲 SKELETON (ready to implement)
- **Providers:**
  - **Coinbase Commerce** - Bitcoin, Ethereum, USDC, Dogecoin
  - **Direct Bitcoin** - Native BTC address generation

### 3. Configuration

**File:** `admin_api/utils/payment_config.py`

```python
# Enable payment providers
PAYMENT_PROVIDERS_ENABLED = {
    PaymentProviderType.REVENUECAT: True,  # ✅ Mobile IAP
    PaymentProviderType.PAPARA: False,     # 🔲 Not yet implemented
    PaymentProviderType.CRYPTO: False,     # 🔲 Not yet implemented
}

# Pricing tiers (purchasing power parity)
PRICING_TIERS = {
    'Tier A': {'regions': ['China', 'India'], 'monthly_usd': 0.99},
    'Tier B': {'regions': ['Middle East'], 'monthly_usd': 1.99},
    'Tier C': {'regions': ['Japan', 'Korea'], 'monthly_usd': 4.99},
    'Tier D': {'regions': ['USA', 'Canada'], 'monthly_usd': 12.99},
    'Tier E': {'regions': ['EU'], 'monthly_usd': 9.99},
}
```

### 4. Gateway Factory Pattern

```python
from admin_api.utils.payment_gateway_abstract import PaymentGatewayFactory, PaymentProviderType

# Get a registered gateway
gateway = PaymentGatewayFactory.get_gateway(PaymentProviderType.PAPARA)

# Check available methods
available = PaymentGatewayFactory.list_available_gateways()
# {'revenuecat': True, 'papara': False, 'crypto': False, ...}
```

## Current Implementation Status

### ✅ FULLY IMPLEMENTED

**RevenueCat Mobile In-App Purchase**
- Integrated into React Native mobile app (`PurchaseService.js`)
- Backend verification endpoints created
- MongoDB subscription tracking
- Feature access control based on plan
- User plan sync from RevenueCat

### 🔲 SKELETON READY (Future Implementation)

**E-Wallets (Papara, Tuum)**
- Abstract classes defined
- API endpoint stubs with comments
- Ready to implement when business needs arise
- No breaking changes needed

**Cryptocurrency (Coinbase Commerce)**
- Abstract classes defined
- Coinbase Commerce integration outlined
- Direct Bitcoin address generation skeleton
- Conversion rate lookup skeleton
- Ready when/if adoption is needed

### ⏳ NOT YET STARTED

- Stripe web payment processing
- PayPal integration
- iyzico integration
- Local payment methods (SEPA, iDEAL, WeChat Pay, Alipay)

## How to Implement a New Payment Provider

### Step 1: Create Implementation Class

```python
# In payment_gateways_[type].py

from admin_api.utils.payment_gateway_abstract import BasePaymentGateway

class MyPaymentGateway(BasePaymentGateway):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.provider_type = PaymentProviderType.MY_PROVIDER

    async def process_payment(self, user_id, amount, currency, payment_method_id, metadata):
        # Implement charge logic
        return PaymentTransaction(...)

    async def refund_payment(self, transaction_id, amount, reason):
        # Implement refund logic
        return PaymentTransaction(...)

    # ... implement other abstract methods
```

### Step 2: Register in Config

```python
# In payment_config.py

if PAYMENT_PROVIDERS_ENABLED[PaymentProviderType.MY_PROVIDER]:
    if PAYMENT_API_KEYS[PaymentProviderType.MY_PROVIDER]:
        from admin_api.utils.payment_gateways_custom import MyPaymentGateway
        
        gateway = MyPaymentGateway(
            api_key=PAYMENT_API_KEYS[PaymentProviderType.MY_PROVIDER]
        )
        PaymentGatewayFactory.register_gateway(PaymentProviderType.MY_PROVIDER, gateway)
```

### Step 3: Use in Views

```python
# In admin_api/views/payment_views.py

gateway = PaymentGatewayFactory.get_gateway(PaymentProviderType.MY_PROVIDER)
transaction = await gateway.process_payment(user_id, amount, currency, method_id)
```

## Payment Flow Diagrams

### Mobile In-App Purchase (RevenueCat)
```
User (iOS/Android App)
    ↓
    App Store / Play Store
    ↓
    RevenueCat SDK (automatic)
    ↓
    PurchaseService.js (getSubscriptionStatus)
    ↓
    Backend: VerifySubscriptionView
    ↓
    RevenueCat API (verify receipt)
    ↓
    MongoDB (update user plan + subscription)
    ↓
    FeatureAccessView (check premium features)
```

### E-Wallet Payment (Future - Papara Example)
```
User (Mobile/Web)
    ↓
    Papara Login Flow
    ↓
    PaparaPaymentGateway.initiate_wallet_payment()
    ↓
    Papara API (charge wallet)
    ↓
    Webhook: Papara → Backend
    ↓
    MongoDB (update subscription)
```

### Cryptocurrency Payment (Future)
```
User
    ↓
    CoinbaseCommerceGateway.create_payment_address()
    ↓
    Display Bitcoin/Ethereum Address
    ↓
    User sends crypto to address
    ↓
    Blockchain confirmation (async)
    ↓
    Webhook: Coinbase → Backend
    ↓
    MongoDB (update subscription)
```

## Database Schema

### user_subscriptions Collection

```javascript
{
  user_id: 123,
  plan: "premium",  // free, premium
  provider: "revenuecat",  // stripe, papara, crypto, etc.
  
  // RevenueCat fields
  entitlements: {"premium": true},
  subscriptions: {"monthly_tier_c": true},
  
  // Generic fields
  original_purchase_date: "2026-04-19T...",
  expires_date: "2026-05-19T...",
  
  // Payment tracking
  payment_status: "completed",  // pending, completed, failed, refunded
  transaction_ids: ["rc_123", "stripe_456"],
  
  // Dates
  verified_at: "2026-04-19T...",
  cancelled_at: null,
  refunded_at: null,
}
```

### payment_transactions Collection

```javascript
{
  user_id: 123,
  provider: "revenuecat",
  amount: 4.99,
  currency: "USD",
  status: "completed",  // pending, processing, completed, failed, refunded
  transaction_id: "rc_ch_123",
  reference_id: "papara_xyz",  // Optional provider-specific ref
  
  metadata: {
    plan: "monthly_tier_c",
    region: "Asia-Pacific",
    country_code: "JP",
    ip_address: "203.0.113.42",
  },
  
  created_at: "2026-04-19T12:30:00Z",
  completed_at: "2026-04-19T12:32:00Z",
  refunded_at: null,
}
```

## Environment Variables

```bash
# RevenueCat (Mobile IAP) ✅ IMPLEMENTED
REVENUECAT_API_KEY=sk_test_xxxxx
PAYMENT_REVENUECAT_ENABLED=True

# E-Wallets (Future)
PAPARA_API_KEY=papara_test_key_xxx
PAYMENT_PAPARA_ENABLED=False
TUUM_API_KEY=tuum_test_key_xxx
TUUM_MERCHANT_ID=merchant_123
PAYMENT_TUUM_ENABLED=False

# Cryptocurrency (Future)
COINBASE_COMMERCE_API_KEY=xxxx
PAYMENT_CRYPTO_ENABLED=False

# Stripe (Future)
STRIPE_API_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
PAYMENT_STRIPE_ENABLED=False

# iyzico (Future)
IYZICO_API_KEY=sandbox_key_xxx
IYZICO_SECRET_KEY=sandbox_secret_xxx
PAYMENT_IYZICO_ENABLED=False

# PayPal (Future)
PAYPAL_API_KEY=paypal_key_xxx
PAYMENT_PAYPAL_ENABLED=False
```

## Testing Payment Providers

### RevenueCat (Already Active)
```bash
# Test subscription verification
curl -X POST http://localhost:8000/api/subscription/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "fetch_token": "rc_test_token",
    "is_ios": true
  }'

# Test feature access
curl http://localhost:8000/api/subscription/feature/123/?feature=unlimited_checks
```

### Future Providers (When Implemented)
```bash
# Test Papara payment
# gateway = PaparaPaymentGateway(api_key='...')
# result = await gateway.process_payment(user_id, 4.99, 'TRY', '...')

# Test crypto payment
# gateway = CoinbaseCommerceGateway(api_key='...')
# address_info = await gateway.create_payment_address(user_id, 4.99, 'bitcoin')
```

## Security Considerations

1. **API Key Protection**
   - Store in environment variables, not code
   - Rotate periodically
   - Use provider-specific test/production keys

2. **Receipt Verification**
   - Always verify with provider API (RevenueCat, App Store, Play Store)
   - Never trust client-side receipt data
   - Store verification timestamp

3. **Webhook Security**
   - Verify webhook signatures using WEBHOOK_SECRETS
   - Check timestamp to prevent replay attacks
   - Use HTTPS only

4. **User Data Protection**
   - PCI compliance for card payments (delegated to Stripe/iyzico)
   - GDPR compliance for payment records
   - Encrypt sensitive data in database

5. **Fraud Prevention**
   - Monitor duplicate transactions from same user
   - Flag suspicious patterns (multiple refunds, chargebacks)
   - Verify IP addresses when suspicious

## Monitoring & Alerts

### Health Checks
```python
from admin_api.utils.payment_config import initialize_payment_gateways
from admin_api.utils.payment_gateway_abstract import PaymentGatewayFactory, PaymentProviderType

# In monitoring/health views:
gateway = PaymentGatewayFactory.get_gateway(PaymentProviderType.REVENUECAT)
is_healthy = await gateway.health_check()
```

### Logs to Monitor
```
✓ Payment gateways ready. Available: {...}
✗ RevenueCat verification error: Connection timeout
✗ Payment processing failed: insufficient_funds
⚠️  High refund rate detected for user_id=123
```

## Future Roadmap

- [ ] Stripe card payment integration
- [ ] PayPal integration
- [ ] Papara e-wallet implementation
- [ ] Tuum multi-provider aggregation
- [ ] Cryptocurrency (Coinbase Commerce)
- [ ] Local payment methods (SEPA, iDEAL, WeChat, Alipay)
- [ ] Recurring billing (subscriptions) via Stripe
- [ ] Dunning management (failed payment retries)
- [ ] Multi-currency support (dynamic conversion)
- [ ] Analytics dashboard (revenue, churn, LTV)
