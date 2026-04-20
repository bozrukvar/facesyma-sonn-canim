# Phase 1: Freemium Integration

**Status:** ✅ Designed & Ready  
**Launch:** Free (Month 1-3) → Freemium (Month 4+)  
**Revenue Model:** Subscription-based SaaS  

---

## 🔄 How Freemium Integrates with Phase 1

### **Current System (Month 1-3): ALL FREE**

```
Compatibility Module:
├─ ✅ calculate_compatibility() — UNLIMITED
├─ ✅ find_compatible_users() — UNLIMITED
└─ ✅ Conflict detection — UNLIMITED

Communities:
├─ ✅ auto_add_to_communities() — UNLIMITED
├─ ✅ List/browse communities — UNLIMITED
├─ ✅ Join community — UNLIMITED
└─ ✅ Send community chat — UNLIMITED (invited members)

Messaging:
├─ ✅ Direct messages — UNLIMITED
├─ ✅ File sharing — UNLIMITED
└─ ✅ Group creation — UNLIMITED

Goal: Build to 10K+ active users
Strategy: All features free, establish network
```

### **Enhanced System (Month 4+): FREEMIUM**

```
FREE TIER (Limit-based):
├─ Compatibility checks: 3/month ⚠️ LIMIT
├─ Community joins: 1 ⚠️ LIMIT
├─ Direct messages: 10/month ⚠️ LIMIT
├─ File sharing: None ❌ LOCKED
└─ Features: Read-only access

PREMIUM TIER ($9.99/month):
├─ Compatibility checks: UNLIMITED ✅
├─ Community joins: UNLIMITED ✅
├─ Direct messages: UNLIMITED ✅
├─ File sharing: 50MB/month ✅
└─ Features: Full access ✅
```

---

## 📋 Feature-by-Feature Paywall

### **Compatibility Module**

| Feature | Free | Premium |
|---------|------|---------|
| View compatibility score | ✅ Yes | ✅ Yes |
| Check 2 users per month | ✅ 3/month | ✅ Unlimited |
| Find compatible users | ✅ Limited | ✅ Unlimited |
| Advanced filters | ❌ No | ✅ Yes |
| See match reasons | ✅ Yes | ✅ Yes |
| Messaging capability | ⚠️ 10/mo | ✅ Unlimited |

### **Communities**

| Feature | Free | Premium |
|---------|------|---------|
| Browse communities | ✅ Yes | ✅ Yes |
| View members | ✅ Yes | ✅ Yes |
| Join 1st community | ✅ Yes | ✅ Yes |
| Join additional | ❌ Limited | ✅ Unlimited |
| See pending invitations | ✅ Yes | ✅ Yes |
| Approve community invite | ✅ Yes | ✅ Yes |
| Community chat (read) | ✅ Yes | ✅ Yes |
| Community chat (write) | ⚠️ 10/mo | ✅ Unlimited |

### **Messaging (Future: Phase 2)**

| Feature | Free | Premium |
|---------|------|---------|
| View 1:1 messages | ✅ Limited | ✅ Unlimited |
| Send 1:1 messages | ⚠️ 10/mo | ✅ Unlimited |
| File sharing | ❌ No | ✅ Yes (50MB) |
| Voice messages | ❌ No | ✅ Yes |
| Message history | ⚠️ 30 days | ✅ Unlimited |

---

## 🔧 Implementation Guide

### **Step 1: Add Subscription Check to Views**

```python
# compatibility_views.py - Modified views

from functools import wraps
from admin_api.utils.mongo import get_subscription_col

def require_premium_feature(feature_name):
    """Decorator to check if user has premium or free tier limit"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            user_id = _get_user_id(request)
            
            if not user_id:
                # Anonymous users: proceed (may be handled later)
                return view_func(self, request, *args, **kwargs)
            
            # Check subscription
            subscription = get_user_subscription(user_id)
            
            if subscription['tier'] == 'premium':
                # Premium users: allow everything
                return view_func(self, request, *args, **kwargs)
            
            # Free tier: check limits
            if not check_free_tier_limit(user_id, feature_name):
                return JsonResponse({
                    'detail': f'Free tier limit reached for {feature_name}',
                    'upgrade_url': '/api/v1/subscription/upgrade/',
                    'upgrade_price': '$9.99/month'
                }, status=402)  # Payment Required
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


# Modified CheckCompatibilityView
@method_decorator(csrf_exempt, name='dispatch')
class CheckCompatibilityView(View):
    
    def post(self, request):
        user_id = _get_user_id(request)
        
        # ✅ NEW: Check free tier limit
        if user_id:
            sub = get_user_subscription(user_id)
            if sub['tier'] == 'free':
                used = count_monthly_checks(user_id)
                if used >= 3:
                    return JsonResponse({
                        'detail': 'Free tier limit (3/month)',
                        'used': used,
                        'limit': 3,
                        'status_code': 402
                    }, status=402)
        
        # ... rest of function unchanged
```

### **Step 2: Add Subscription Helper Functions**

```python
# admin_api/utils/subscription.py (NEW FILE)

def get_user_subscription(user_id: int) -> dict:
    """Get user's subscription status"""
    db = _get_db()
    
    sub = db['user_subscriptions'].find_one({'user_id': user_id})
    
    if not sub:
        # User never subscribed → default free tier
        return {
            'user_id': user_id,
            'tier': 'free',
            'status': 'active',
            'created_at': time.time()
        }
    
    # Check if expired
    if sub['tier'] == 'premium' and sub['renews_at'] < time.time():
        # Subscription expired → downgrade to free
        db['user_subscriptions'].update_one(
            {'user_id': user_id},
            {'$set': {'tier': 'free', 'status': 'expired'}}
        )
        sub['tier'] = 'free'
    
    return sub


def count_monthly_checks(user_id: int) -> int:
    """Count compatibility checks used this month"""
    db = _get_db()
    
    now = time.time()
    month_ago = now - (30 * 24 * 60 * 60)
    
    count = db['compatibility'].count_documents({
        '$or': [
            {'user1_id': user_id},
            {'user2_id': user_id}
        ],
        'calculated_at': {'$gt': month_ago}
    })
    
    return count


def count_joined_communities(user_id: int) -> int:
    """Count communities user has joined (active status)"""
    db = _get_db()
    
    count = db['community_members'].count_documents({
        'user_id': user_id,
        'status': 'active'
    })
    
    return count


def check_free_tier_limit(user_id: int, feature: str) -> bool:
    """Check if free tier limit exceeded"""
    
    if feature == 'compatibility_check':
        return count_monthly_checks(user_id) < 3
    
    elif feature == 'community_join':
        return count_joined_communities(user_id) < 1
    
    elif feature == 'direct_message':
        # Count messages this month
        db = _get_db()
        now = time.time()
        month_ago = now - (30 * 24 * 60 * 60)
        
        count = db['community_messages'].count_documents({
            'from_user_id': user_id,
            'created_at': {'$gt': month_ago}
        })
        
        return count < 10
    
    else:
        return True  # Unknown feature: allow
```

### **Step 3: Add Subscription Endpoints**

```python
# compatibility_views.py - NEW ENDPOINTS

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionStatusView(View):
    """GET /api/v1/subscription/status/?user_id=123"""
    
    def get(self, request):
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return JsonResponse({'detail': 'user_id required'}, status=400)
        
        sub = get_user_subscription(int(user_id))
        
        # Build usage info
        usage = {
            'compatibility_checks': {
                'used': count_monthly_checks(int(user_id)),
                'limit': 3 if sub['tier'] == 'free' else None
            },
            'communities_joined': {
                'used': count_joined_communities(int(user_id)),
                'limit': 1 if sub['tier'] == 'free' else None
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'tier': sub['tier'],
                'status': sub.get('status', 'active'),
                'renews_at': sub.get('renews_at'),
                'usage': usage,
                'features': {
                    'unlimited_messaging': sub['tier'] == 'premium',
                    'unlimited_communities': sub['tier'] == 'premium',
                    'file_sharing': sub['tier'] == 'premium'
                }
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionUpgradeView(View):
    """POST /api/v1/subscription/upgrade/"""
    
    def post(self, request):
        data = json.loads(request.body)
        user_id = data.get('user_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # TODO: Integrate with Stripe/iyzico payment processor
        # For now: return checkout URL (mock)
        
        return JsonResponse({
            'success': True,
            'data': {
                'checkout_url': 'https://checkout.stripe.com/pay/mock_session',
                'price': '$9.99/month' if billing_cycle == 'monthly' else '$89/year',
                'message': 'Redirect to checkout page'
            }
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionCancelView(View):
    """POST /api/v1/subscription/cancel/"""
    
    def post(self, request):
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        db = _get_db()
        
        db['user_subscriptions'].update_one(
            {'user_id': user_id},
            {'$set': {
                'tier': 'free',
                'status': 'cancelled',
                'ended_at': time.time()
            }}
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'message': 'Subscription cancelled',
                'tier': 'free',
                'status': 'cancelled'
            }
        })
```

### **Step 4: Update URLs**

```python
# urls.py - NEW ROUTES

path('subscription/status/',   SubscriptionStatusView.as_view(),   name='subscription-status'),
path('subscription/upgrade/',  SubscriptionUpgradeView.as_view(),  name='subscription-upgrade'),
path('subscription/cancel/',   SubscriptionCancelView.as_view(),   name='subscription-cancel'),
```

---

## 📊 Database Changes

### **New Collection: user_subscriptions**

```javascript
db.createCollection("user_subscriptions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "tier", "status"],
      properties: {
        _id: { bsonType: "objectId" },
        user_id: { bsonType: "int" },
        tier: { enum: ["free", "premium"] },
        status: { enum: ["active", "cancelled", "expired"] },
        subscription_id: { bsonType: "string" },
        created_at: { bsonType: "date" },
        started_at: { bsonType: "date" },
        renews_at: { bsonType: "date" },
        price: { bsonType: "double" },
        billing_cycle: { enum: ["monthly", "yearly"] },
        auto_renew: { bsonType: "bool" }
      }
    }
  }
})

// Indexes
db.user_subscriptions.createIndex({ user_id: 1 }, { unique: true })
db.user_subscriptions.createIndex({ tier: 1 })
db.user_subscriptions.createIndex({ status: 1 })
db.user_subscriptions.createIndex({ renews_at: 1 })
```

---

## 🎯 Timeline

### **Phase 1.0 (Current - Month 1-3)**
- ✅ All features FREE (unlimited)
- ✅ Build user base (10K+ goal)
- ✅ Analyze usage patterns

### **Phase 1.1 (Month 4)**
- ✅ Subscription system live
- ✅ Feature paywall (free tier limits)
- ✅ Upgrade prompts in UI
- ✅ No real payment yet (mock checkout)

### **Phase 1.2 (Month 5)**
- ✅ Stripe integration
- ✅ iyzico integration (Turkey)
- ✅ Real payments live
- ✅ Billing history

---

## 📱 User Experience Flow

### **Free User Upgrading**

```
1. Free user hits limit (3 checks used)
   └─ "Free tier limit reached"
   
2. Click "Upgrade to Premium"
   └─ See pricing: $9.99/month
   
3. Click "Upgrade"
   └─ Redirect to Stripe checkout
   
4. Complete payment
   └─ Subscription created
   
5. Instantly get premium features
   └─ Unlimited checks, communities, messages
```

---

## ✅ Checklist

- [ ] user_subscriptions collection created
- [ ] Feature paywall logic in views
- [ ] Free tier limits enforced
- [ ] Subscription helper functions
- [ ] /subscription/status endpoint
- [ ] /subscription/upgrade endpoint
- [ ] /subscription/cancel endpoint
- [ ] UI upgrade prompts
- [ ] Tests: free vs premium flows
- [ ] Documentation updated
- [ ] Metrics dashboard

---

**Status:** ✅ Design Complete  
**Implementation:** Month 4  
**Revenue Start:** Month 4-5  
**Target:** 5-10% conversion → $5-10K MRR by Month 6
