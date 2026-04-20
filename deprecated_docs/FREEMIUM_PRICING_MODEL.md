# Freemium Pricing Model

**Status:** ✅ Designed for Phase 1  
**Launch:** Month 1 (Free) → Month 4 (Freemium)  
**Target:** 5-10% premium conversion  

---

## 📊 Pricing Tiers

### **FREE TIER** (Always Available)
```
Price: $0/month

Features:
├─ Compatibility check: 3/ay (per user)
├─ Community browse: Unlimited (read-only)
├─ Community join: Sınırlı (ilk 1 topluluk free)
├─ Direct message: 10 msg/ay (text only)
├─ Profile visibility: Public
├─ Community chat: Read-only access
└─ Ads: Yes (lower priority in recommendations)

Limits:
├─ Max 1 joined community
├─ Max 10 messages/month
├─ Max 3 compatibility checks/month
└─ Basic search only
```

### **PREMIUM TIER** ($9.99/month or $89/year)
```
Price: $9.99/month | $89/year (Savings: 26%)

Features:
✅ Everything in FREE +
├─ Unlimited compatibility checks
├─ Unlimited community joins (500 max)
├─ Unlimited direct messages
├─ File sharing (50MB/month limit)
├─ Priority in recommendations
├─ See who visited profile
├─ Advanced search filters
├─ Remove ads
├─ Early access to new features
├─ Priority customer support
└─ Monthly insights report

Limits:
├─ Max 500 communities joined
├─ Max 50MB file storage/month
├─ Unlimited messaging
└─ No ads
```

---

## 🔑 Feature Paywall Implementation

### **Current Features (Phase 1)**

```
ALWAYS FREE:
├─ View compatibility score
├─ Browse communities
├─ See community members (public)
├─ Create user profile
├─ View own analysis results
└─ Leave community (if joined)

PREMIUM ONLY:
├─ Join multiple communities (>1)
├─ Send direct messages (>10/month)
├─ Share files/media
├─ See advanced stats
├─ See who visited profile
└─ Priority support
```

### **Feature Access Logic**

```python
# compatibility_views.py'da eklenecek

def check_premium(user_id, feature):
    """Check if user has access to feature"""
    user_subscription = get_user_subscription(user_id)
    
    if feature == 'unlimited_messages':
        return user_subscription['tier'] == 'premium'
    
    elif feature == 'unlimited_communities':
        return user_subscription['tier'] == 'premium'
    
    elif feature == 'file_sharing':
        return user_subscription['tier'] == 'premium'
    
    elif feature == 'compatibility_check':
        if user_subscription['tier'] == 'premium':
            return True
        # Free tier: 3/month
        return get_monthly_checks(user_id) < 3
    
    elif feature == 'community_join':
        if user_subscription['tier'] == 'premium':
            return True
        # Free tier: 1 community
        joined_count = get_joined_communities(user_id)
        return joined_count < 1
    
    else:
        return True  # Default: allow
```

---

## 🗄️ Database Schema Changes

### **New Collection: user_subscriptions**

```javascript
{
  _id: ObjectId,
  user_id: Number,
  tier: String,                    // 'free' | 'premium'
  status: String,                  // 'active' | 'cancelled' | 'expired'
  
  // Subscription Details
  subscription_id: String,         // Stripe/iyzico ref
  created_at: Timestamp,
  started_at: Timestamp,
  ended_at: Timestamp,
  renews_at: Timestamp,
  
  // Pricing
  price: Number,                   // $9.99
  currency: String,                // 'USD' | 'TRY'
  billing_cycle: String,           // 'monthly' | 'yearly'
  
  // Payment Info
  payment_method: String,          // 'stripe' | 'iyzico' | 'credit_card'
  last_4_digits: String,
  
  // Usage Tracking (Free Tier)
  monthly_checks_used: Number,     // Current month usage
  checks_reset_date: Timestamp,    // When resets to 0
  communities_joined: Number,
  
  // Preferences
  auto_renew: Boolean,
  discount_code: String
}
```

### **Update: user_profiles Collection**

```javascript
// Add these fields to existing user_profiles
{
  user_id: Number,
  subscription_tier: String,       // 🆕 'free' | 'premium'
  subscription_status: String,     // 🆕 'active' | 'expired'
  subscription_expires: Timestamp, // 🆕
  // ... existing fields
}
```

---

## 📡 API Endpoints (Phase 1 + Freemium)

### **Existing Endpoints with Paywall**

All existing endpoints now check subscription:

```python
@method_decorator(csrf_exempt, name='dispatch')
class CheckCompatibilityView(View):
    def post(self, request):
        user_id = _get_user_id(request)
        
        # ✅ NEW: Check free tier limit
        if user_id:
            sub = get_user_subscription(user_id)
            if sub['tier'] == 'free':
                checks_used = get_monthly_checks(user_id)
                if checks_used >= 3:
                    return JsonResponse({
                        'detail': 'Free tier limit reached (3/month). Upgrade to premium.',
                        'limit': 3,
                        'used': checks_used,
                        'upgrade_url': '/api/v1/subscribe/'
                    }, status=402)  # Payment Required
        
        # ... rest of logic
```

---

## 💳 New Endpoints for Subscription Management

### **1. Get User Subscription Status**
```bash
GET /api/v1/subscription/status/?user_id=123

Response:
{
  "success": true,
  "data": {
    "tier": "free",
    "status": "active",
    "renews_at": null,
    "features": {
      "unlimited_messages": false,
      "unlimited_communities": false,
      "file_sharing": false,
      "advanced_search": false
    },
    "usage": {
      "compatibility_checks": {
        "used": 1,
        "limit": 3,
        "resets": "2026-05-14"
      },
      "communities_joined": {
        "used": 1,
        "limit": 1
      }
    }
  }
}
```

### **2. Upgrade to Premium**
```bash
POST /api/v1/subscription/upgrade/

Request:
{
  "user_id": 123,
  "billing_cycle": "monthly",  // or "yearly"
  "payment_method": "stripe"   // or "iyzico"
}

Response:
{
  "success": true,
  "data": {
    "checkout_url": "https://checkout.stripe.com/...",
    "session_id": "cs_live_..."
  }
}
```

### **3. Cancel Subscription**
```bash
POST /api/v1/subscription/cancel/

Request:
{
  "user_id": 123
}

Response:
{
  "success": true,
  "data": {
    "tier": "free",
    "status": "cancelled",
    "effective_date": "2026-04-15"
  }
}
```

---

## 💰 Pricing Logic (Optional: Future)

```python
# Currency ve country'ye göre pricing
PRICING = {
    'USD': {
        'monthly': 9.99,
        'yearly': 89.00  # 26% saving
    },
    'TRY': {
        'monthly': 199,
        'yearly': 1790   # 26% saving
    },
    'EUR': {
        'monthly': 8.99,
        'yearly': 80.91
    }
}

# Discount codes
DISCOUNT_CODES = {
    'EARLY2026': {
        'discount_percent': 50,
        'valid_until': '2026-06-01',
        'max_uses': 1000
    },
    'ANNUAL20': {
        'discount_percent': 20,
        'valid_until': '2026-12-31',
        'applies_to': 'yearly'
    }
}
```

---

## 📋 Implementation Phases

### **Phase 1.0 (Current):** All Free
```
✅ All features available for free
✅ No subscription system
✅ Build user base (target: 10K)
✅ Analyze usage patterns
├─ Which features most used?
├─ User retention patterns?
├─ Engagement metrics?
└─ Network maturity level?

Timeline: Month 1-3
Goal: 10K+ active users
```

### **Phase 1.1 (Month 4):** Freemium Launches
```
✅ User subscription collection created
✅ Feature paywall implemented
✅ Pricing displayed in UI
✅ Upgrade prompts added
✅ Payment integration (stub for now)

Timeline: Month 4
Conversion Target: 2-3% (conservative)
Expected MRR: $600-1,500 (30-50 premium users)
```

### **Phase 1.2 (Month 5):** Payment Integration
```
✅ Stripe integration live
✅ iyzico integration live (Turkey)
✅ Billing history tracking
✅ Invoice generation
✅ Churn analysis

Timeline: Month 5-6
Conversion Target: 5-8%
Expected MRR: $2,500-4,000 (250-400 premium users)
```

---

## 🎯 Business Metrics to Track

### **Free Tier Metrics**
```
├─ Free users: Total count
├─ Monthly active: % of free users active
├─ Feature usage: Most used features
├─ Time to upgrade: Days before premium conversion
├─ Churn rate: % free users churning
└─ LTV (Lifetime): Free user value in referrals
```

### **Premium Tier Metrics**
```
├─ Premium subscribers: Total count
├─ MRR: Monthly recurring revenue
├─ Churn rate: % upgraders cancelling
├─ CAC: Cost to acquire 1 premium user
├─ LTV: Lifetime value of premium user
├─ NRR: Net revenue retention (upsells)
└─ ARPU: Average revenue per user (all)
```

---

## 📊 Financial Projections (Freemium)

### **Year 1: Conservative Scenario**

```
Month 1-3 (Free):
├─ Active Users: 2K → 10K
├─ Revenue: $0
└─ Goal: Build network

Month 4-6 (Freemium Launch):
├─ Active Users: 10K → 20K
├─ Premium Users: 3-5% = 600-1000
├─ MRR: $600 × $9.99 = $6K
├─ Revenue Q2: $18K

Month 7-12 (Growth):
├─ Active Users: 20K → 50K
├─ Premium Users: 5-8% = 2,500-4,000
├─ MRR: $3-4K (growing)
├─ Revenue H2: $40-50K

TOTAL Year 1: $58-68K revenue
```

### **Year 1: Optimistic Scenario**

```
Month 1-3: Same (network building)

Month 4-6:
├─ Active Users: 10K → 30K
├─ Premium: 5% = 1,500
├─ MRR: $15K
├─ Revenue Q2: $45K

Month 7-12:
├─ Active Users: 30K → 100K
├─ Premium: 7% = 7,000
├─ MRR: $70K
├─ Revenue H2: $350K

TOTAL Year 1: $395K revenue
```

---

## 🔐 Fraud Prevention

```python
# Premium verification on every API call
def verify_premium_access(user_id, feature):
    """Verify user has premium or feature available"""
    
    # 1. Check subscription status
    sub = db.user_subscriptions.find_one({
        'user_id': user_id,
        'status': 'active'
    })
    
    if not sub:
        return check_free_tier_limit(user_id, feature)
    
    # 2. Verify subscription not expired
    if sub['renews_at'] < now():
        # Subscription expired
        return check_free_tier_limit(user_id, feature)
    
    # 3. Grant premium access
    return True

# All feature access goes through this
```

---

## 📱 UI/UX Considerations

### **Upgrade Prompts**

```
When free tier limit reached:

┌──────────────────────────────────┐
│  Limit Reached                   │
├──────────────────────────────────┤
│  You've used 3/3 compatibility  │
│  checks this month.             │
│                                  │
│  Upgrade to Premium for:         │
│  ✓ Unlimited checks             │
│  ✓ Unlimited communities        │
│  ✓ Direct messaging             │
│                                  │
│  [UPGRADE TO PREMIUM - $9.99/mo] │
│  [Not now]                       │
└──────────────────────────────────┘
```

### **Feature Lock Indicators**

```
Locked Features Show:
├─ 🔒 Feature name
├─ Premium required message
├─ Price: $9.99/month
└─ [Unlock] button
```

---

## ✅ Checklist for Phase 1.1

- [ ] user_subscriptions collection created
- [ ] Feature paywall logic added to views
- [ ] Free tier limits enforced
- [ ] /subscription/status endpoint
- [ ] /subscription/upgrade endpoint (mock payment)
- [ ] /subscription/cancel endpoint
- [ ] UI prompts for upgrades
- [ ] Usage tracking implemented
- [ ] Monthly reset logic
- [ ] Metrics dashboard
- [ ] Documentation
- [ ] Testing (free vs premium flows)

---

## 🚀 Summary

```
TIMELINE:
├─ Month 1-3: Free (all features)
├─ Month 4: Freemium launches (feature paywall)
├─ Month 5: Real payments (Stripe/iyzico)
└─ Month 6+: Growth & optimization

CONVERSION:
├─ Target: 5-10% premium conversion
├─ MRR by Month 6: $5-10K
├─ Year 1 Revenue: $50-400K (depending on growth)

BENEFITS:
✅ Network effect from free users
✅ High engagement (premium users pay)
✅ Sustainable business model
✅ Competitive advantage
✅ Flexible for future tiers
```

---

**Status:** ✅ Ready for Implementation  
**Next Step:** Build feature paywall logic in Phase 1.1  
**Payment Processing:** Month 5
