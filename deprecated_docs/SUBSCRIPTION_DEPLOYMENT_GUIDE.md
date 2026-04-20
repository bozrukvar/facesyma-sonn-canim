# Subscription System Deployment Guide

**Status:** ✅ READY (Phase 1.1 Launch - Month 4)  
**Date:** 2026-04-14

---

## 🚀 Quick Start

### 1. Database Verification
```bash
# Check if user_subscriptions collection exists
python migrate_subscriptions.py

# Expected output:
# ✅ Indexes created: user_id (unique), tier, status, renews_at
```

### 2. Test Subscription Endpoints
```bash
# Check free tier user status
curl -X GET "http://localhost:8000/api/v1/subscription/status/?user_id=123"

# Response:
{
  "success": true,
  "data": {
    "tier": "free",
    "status": "active",
    "features": {
      "unlimited_messaging": false,
      "unlimited_communities": false,
      "file_sharing": false
    },
    "usage": {
      "compatibility_checks": {
        "used": 1,
        "limit": 3
      },
      "communities_joined": {
        "used": 0,
        "limit": 1
      }
    }
  }
}
```

### 3. Upgrade Flow
```bash
# User initiates upgrade
curl -X POST "http://localhost:8000/api/v1/subscription/upgrade/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "billing_cycle": "monthly"
  }'

# Response (Month 4: Mock checkout):
{
  "success": true,
  "data": {
    "checkout_url": "https://checkout.stripe.com/pay/mock_session_123",
    "price": "$9.99/month",
    "billing_cycle": "monthly"
  }
}

# After Month 5 (Real Stripe/iyzico):
# User completes payment → subscription_id stored
# Subscription status updated to 'active' + renews_at set
```

---

## 🔧 Implementation Phases

### Month 1-3: FREE (No Subscription Needed)
```
All features unlimited.
No API calls to subscription endpoints.
```

### Month 4: FREEMIUM LAUNCH (Feature Paywall)
```
1. Feature paywall activated:
   - POST /api/v1/compatibility/check/ returns 402 if limit hit
   - POST /api/v1/communities/<id>/join/ returns 402 if limit hit
   - Free tier checks count from MongoDB

2. UI Integration:
   - Show "Free tier limit reached" popup
   - Display "Upgrade to Premium for $9.99/month" button
   - Link to POST /api/v1/subscription/upgrade/

3. Mock Checkout:
   - Stripe checkout page (mock URL)
   - No real payment processing
   - Monitor conversion metrics

4. Target: 2-3% conversion rate = 20-30 premium users from 1000 free users
```

### Month 5: REAL PAYMENTS (Stripe + iyzico)
```
1. Stripe Integration:
   - Replace mock checkout with real Stripe Checkout
   - Handle webhook: payment_intent.succeeded
   - Create subscription record in user_subscriptions
   - Set renews_at = now + billing_cycle

2. iyzico Integration (Turkey):
   - Alternative payment method for Turkish users
   - Detect country from IP/profile
   - Route to iyzico checkout if user is in Turkey
   - Handle iyzico webhooks

3. Subscription Management:
   - Automatic renewal 1 day before renews_at
   - Failed payment → 3-day retry
   - Auto-downgrade if payment fails 3x
   - Send renewal reminders 7 days before

4. Target: 5-10% conversion rate = 500-1000 premium users from 10K free users
```

---

## 📋 Database Structure

### user_subscriptions Collection
```javascript
{
  _id: ObjectId,
  user_id: Number (unique index),
  tier: String,                    // 'free' | 'premium'
  status: String,                  // 'active' | 'expired' | 'cancelled'
  
  // Subscription Details
  subscription_id: String,         // Stripe/iyzico reference ID
  created_at: Timestamp,           // When account created
  started_at: Timestamp,           // When premium started
  renews_at: Timestamp,            // When next charge happens
  ended_at: Timestamp,             // When cancelled (if applicable)
  
  // Pricing
  price: Number,                   // 9.99 (dollars) or 199 (Turkish Lira)
  currency: String,                // 'USD' | 'TRY'
  billing_cycle: String,           // 'monthly' | 'yearly'
  
  // Payment Info
  payment_method: String,          // 'stripe' | 'iyzico'
  last_4_digits: String,           // Credit card last 4 digits
  
  // Auto-renewal
  auto_renew: Boolean,             // Default: true
  failed_attempts: Number,         // Failed payments count
  
  // Discount (Optional)
  discount_code: String,           // 'EARLY2026', 'ANNUAL20'
  discount_percent: Number         // 20, 50, etc
}
```

---

## 🔒 Free Tier Limit Enforcement

### Implementation Pattern
```python
# In views, before processing request:

from compatibility_views import (
    get_user_subscription,
    check_free_tier_limit,
    require_premium_feature
)

# Method 1: Check manually
sub = get_user_subscription(user_id)
if sub['tier'] == 'free':
    if not check_free_tier_limit(user_id, 'compatibility_check'):
        return JsonResponse({
            'detail': 'Free tier limit (3/month) reached',
            'upgrade_url': '/api/v1/subscription/upgrade/'
        }, status=402)  # Payment Required

# Method 2: Use decorator (preferred)
@require_premium_feature('compatibility_check')
def post(self, request):
    # Code here only runs if:
    # - User is premium, OR
    # - User is free AND has not hit limit
    # Decorator returns 402 if limit hit
    ...
```

### Features Subject to Limits
```
Free Tier (Hard Limits):
├─ compatibility_check: 3/month
├─ community_join: 1 active community
├─ direct_message: 10/month
└─ file_sharing: ❌ NOT AVAILABLE

Premium (Unlimited):
├─ compatibility_check: ∞
├─ community_join: ∞ (500 cap)
├─ direct_message: ∞
└─ file_sharing: 50MB/month
```

---

## 💰 Pricing & Revenue

### Price Points
```
$9.99/month (monthly)
$89/year    (yearly = $7.42/month = 26% savings)

Optional (future):
$4.99/month (light tier - limited communities)
$14.99/month (pro tier - priority support)
$49.99/month (enterprise - API access)
```

### Revenue Math
```
Conservative (3% conversion):
├─ 10K free users
├─ 300 premium users
├─ $9.99 × 300 = $3K MRR (Month 4)
└─ Year 1: $70K

Optimistic (7% conversion):
├─ 100K free users
├─ 7,000 premium users
├─ $9.99 × 7,000 = $70K MRR (Month 12)
└─ Year 1: $400K
```

---

## 📊 Metrics to Track

### Free Tier Metrics
```
├─ Total free users
├─ Monthly active free users
├─ Feature usage (checks, communities, messages)
├─ Time to upgrade (days until premium conversion)
└─ Churn rate (free users lost per month)
```

### Premium Tier Metrics
```
├─ Premium subscribers (count)
├─ MRR (Monthly Recurring Revenue)
├─ ARR (Annual Recurring Revenue)
├─ Churn rate (% cancellations/month)
├─ CAC (Cost to acquire premium user)
├─ LTV (Lifetime value = avg revenue / churn)
├─ NRR (Net revenue retention = upsell revenue)
└─ ARPU (Average revenue per user = MRR / total users)
```

### Key Targets
```
Target Conversion Rate:
├─ Month 4: 2-3% (conservative start)
├─ Month 6: 5% (growth phase)
├─ Month 12: 7-10% (mature phase)

Target MRR:
├─ Month 4: $3K
├─ Month 6: $10K
├─ Month 12: $70K

Churn Rate Target:
├─ Monthly: <5% (standard for SaaS)
└─ Annual: <50%
```

---

## 🛠️ Maintenance & Operations

### Monthly Tasks
```
1. Check failed payment attempts
   - Auto-retry 3x over 3 days
   - Email user on 2nd failure
   - Downgrade to free on 3rd failure

2. Renew subscriptions
   - Check renews_at field
   - Charge 1 day before renewal
   - Handle failed payments

3. Monitor churn
   - Calculate monthly churn %
   - Identify cancellation reasons
   - Reach out to churning users

4. Track revenue metrics
   - MRR = sum of all active subscriptions
   - ARR = MRR × 12
   - Update financial dashboard
```

### Quarterly Tasks
```
1. Analyze pricing elasticity
   - Consider $4.99, $7.99, $12.99 price points
   - A/B test conversion rates
   - Optimize for revenue

2. Review tier features
   - Add new features to premium
   - Update free tier limits if needed
   - Communicate changes to users

3. Plan new features
   - Layer in messaging features (Phase 2)
   - Add analytics dashboard
   - Launch group functionality
```

---

## 🔄 Upgrade/Downgrade Flows

### User Upgrades to Premium
```
1. User hits limit (e.g., 3 checks/month used)
2. API returns 402 with upgrade URL
3. UI shows "Upgrade to Premium" button
4. User clicks → POST /api/v1/subscription/upgrade/
5. API returns checkout_url (Stripe/iyzico)
6. User completes payment
7. Payment webhook received:
   subscription_id = cs_live_...
   renews_at = now + 1 month
   tier = 'premium'
   status = 'active'
8. User instantly gains premium features
```

### Subscription Renews Automatically
```
1. 1 day before renews_at:
   - Stripe/iyzico charges customer
   - If success: renews_at updated to now + 1 month
   - If failure: mark failed_attempts = 1

2. Retry logic:
   - Attempt 1: Day -1 before expiry
   - Attempt 2: Day 0 (expiry day) + email
   - Attempt 3: Day +1 + final notice
   - After 3 failures: auto-downgrade to free

3. Downgrade:
   - tier = 'free'
   - status = 'expired'
   - End premium access immediately
   - Email user with retry link
```

### User Cancels Premium
```
1. User clicks "Cancel Subscription"
2. POST /api/v1/subscription/cancel/
3. Confirmation email sent
4. Record:
   status = 'cancelled'
   tier = 'free'
   ended_at = now
5. User loses premium access at end of billing cycle
   (or immediately depending on policy)
```

---

## 🚨 Error Handling

### Status Codes
```
200 OK
├─ Subscription checked successfully
└─ Premium feature accessed

402 Payment Required
├─ Free tier limit exceeded
└─ User must upgrade

400 Bad Request
├─ Missing required parameters
└─ Invalid request format

401 Unauthorized
├─ User not authenticated
└─ JWT token invalid

500 Internal Server Error
├─ Database error
├─ Payment processor error
└─ Subscription check failure
```

### Graceful Degradation
```
If subscription check fails:
├─ Free tier: Allow access (don't block on error)
├─ Premium: Assume 'premium' (favor access over restriction)
└─ Log error for investigation
```

---

## 📱 Frontend Integration

### Checkout Flow
```
1. User sees "Upgrade to Premium" button
   └─ Appears when free tier limit hit

2. Click → Load checkout page:
   - Mobile: Stripe/iyzico mobile checkout
   - Web: Hosted checkout page
   - Embedded: iFrame checkout

3. User enters payment details:
   - Card number
   - Expiry
   - CVV
   - Billing address

4. Success → Redirect to /premium/welcome
   └─ Show "Premium activated!"
   └─ Features now unlimited

5. Failure → Show error message
   └─ "Payment failed. Try again."
   └─ Retry button
```

### UI Components Needed
```
1. Free Tier Badge
   └─ Show "FREE" next to user profile

2. Limit Indicator
   └─ Show "3/3 checks used this month"
   └─ Progress bar

3. Upgrade Button
   └─ "Upgrade to Premium - $9.99/month"
   └─ Prominent CTA

4. Subscription Dashboard
   └─ Show current tier
   └─ Show renewal date
   └─ Show usage stats
   └─ Cancel button

5. Premium Indicator
   └─ Show "PREMIUM" badge
   └─ Highlight unlimited features
```

---

## 🔐 Security Checklist

- [ ] Never store raw credit card data
- [ ] Use Stripe/iyzico tokenization
- [ ] HTTPS only for payment flows
- [ ] Validate subscription status server-side (not client-side)
- [ ] Log all subscription changes
- [ ] Encrypt sensitive data in database
- [ ] Rate-limit upgrade endpoint (prevent abuse)
- [ ] Verify JWT token before processing payments
- [ ] Handle expired subscriptions gracefully
- [ ] Test failed payment scenarios

---

## 📞 Support Processes

### Refund Requests
```
Policy: 14-day money-back guarantee
Process:
1. User requests refund within 14 days
2. Manual review (check for abuse)
3. Full refund to original payment method
4. Downgrade to free tier
5. Send farewell survey
```

### Dunning (Failed Payments)
```
Day 1 (Payment Fails):
└─ Retry payment automatically

Day 2 (Still Failed):
└─ Email: "Payment failed, please update"
└─ Link to update payment method

Day 4 (Still Failed):
└─ Final email: "Subscription will be cancelled"
└─ Urgent update link

Day 5:
└─ Auto-downgrade to free
└─ Send cancellation confirmation
```

### Churn Prevention
```
When cancellation detected:
├─ Show retention offer: "Stay for $4.99/month"
├─ Offer 1-month free trial
├─ Get cancellation reason survey
├─ Send win-back email after 30 days
└─ Track effectiveness
```

---

## 🎯 Go-Live Checklist (Month 4)

- [ ] user_subscriptions collection verified
- [ ] Subscription endpoints tested (curl)
- [ ] Feature paywall tested (hit limit, get 402)
- [ ] Mock checkout page working
- [ ] UI showing upgrade prompts
- [ ] Metrics dashboard ready
- [ ] Support runbook ready
- [ ] Monitoring alerts set up
- [ ] Database backups configured
- [ ] Rollback plan documented

---

## 📚 Related Documentation

- PHASE1_FREEMIUM_INTEGRATION.md — Implementation code examples
- FREEMIUM_PRICING_MODEL.md — Pricing strategy
- IMPLEMENTATION_STATUS_PHASE1.md — Complete feature list
- CONSENT_APPROVAL_SYSTEM.md — User consent system

---

**Status:** ✅ Ready for Month 4 Launch  
**Next Step:** Frontend integration + Stripe setup
