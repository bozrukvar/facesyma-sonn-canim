# Subscription Implementation Guide for Frontend/Mobile

## Quick Start

### 1. Mobile (React Native)

The mobile app uses **RevenueCat** for all in-app purchases. This is automatically handled by the App Store and Google Play, so users never interact with the backend directly for payment.

#### Setup (Already Complete)

1. ✅ `facesyma_mobile/package.json` - Added RevenueCat SDK
2. ✅ `facesyma_mobile/src/services/PurchaseService.js` - Created SDK wrapper
3. ✅ `facesyma_backend/admin_api/views/subscription_views.py` - Created verification endpoints

#### Usage in Mobile Components

```javascript
import PurchaseService from '../services/PurchaseService';

// On app startup (after user login)
await PurchaseService.initialize();
await PurchaseService.setUserID(userID);

// Get available subscription packages (with auto-localized pricing)
const packages = await PurchaseService.getSubscriptionPackages();
// Returns: [
//   {
//     id: 'monthly_tier_c',
//     price: '¥499',  // Automatically localized to user's country
//     currency: 'JPY',
//     duration: 'MONTHLY',
//     title: 'Premium',
//     countryCode: 'JP'
//   },
//   { id: 'yearly_tier_c', price: '¥3,999', ... }
// ]

// User selects and purchases
try {
  const customerInfo = await PurchaseService.purchasePackage('monthly_tier_c');
  // customerInfo contains updated subscription status
  
  // Verify with backend
  await fetch('https://api.facesyma.com/api/subscription/verify/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userID,
      fetch_token: customerInfo.originalAppUserId,
      is_ios: Platform.OS === 'ios'
    })
  });
} catch (error) {
  if (error.userCancelled) {
    console.log('User cancelled purchase');
  } else {
    console.error('Purchase failed:', error);
  }
}

// Check subscription status anytime
const status = await PurchaseService.getSubscriptionStatus();
// Returns: {
//   isPremium: true,
//   activeSubscriptions: ['monthly_tier_c'],
//   entitlements: { 'premium': true },
//   expirationDates: { 'premium': '2026-05-19T...' }
// }

// Check if user has access to specific feature
const hasMealGame = await PurchaseService.hasEntitlement('premium');
if (!hasMealGame) {
  // Show paywall
}

// User can restore past purchases
const restored = await PurchaseService.restorePurchases();
```

#### Showing the Paywall

```javascript
// In your feature component
const FeaturePaywall = ({ feature, onUnlock }) => {
  const [packages, setPackages] = useState([]);
  const [isPurchasing, setIsPurchasing] = useState(false);

  useEffect(() => {
    PurchaseService.getSubscriptionPackages().then(setPackages);
  }, []);

  const handlePurchase = async (packageID) => {
    setIsPurchasing(true);
    try {
      await PurchaseService.purchasePackage(packageID);
      
      // Verify with backend
      await verifySubscription();
      
      // Unlock feature
      onUnlock();
    } catch (error) {
      Alert.alert('Purchase Failed', error.message);
    } finally {
      setIsPurchasing(false);
    }
  };

  return (
    <View style={styles.paywall}>
      <Text>Unlock Premium Features</Text>
      {packages.map(pkg => (
        <TouchableOpacity
          key={pkg.id}
          onPress={() => handlePurchase(pkg.id)}
          disabled={isPurchasing}
        >
          <Text>{pkg.title} - {pkg.price} / {pkg.duration}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};
```

### 2. Backend Integration

#### Verify Subscription Endpoint

**Endpoint:** `POST /api/subscription/verify/`

Called by mobile app after purchase to sync subscription with backend.

```bash
curl -X POST https://api.facesyma.com/api/subscription/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "fetch_token": "rc_app_user_123",
    "is_ios": true
  }'

# Response:
{
  "success": true,
  "plan": "premium",
  "entitlements": ["premium"],
  "expires_date": "2026-05-19T12:30:00Z"
}
```

#### Check Subscription Status

**Endpoint:** `GET /api/subscription/status/<user_id>/`

Check user's current subscription without re-verifying with RevenueCat.

```bash
curl https://api.facesyma.com/api/subscription/status/123/

# Response:
{
  "plan": "premium",
  "active": true,
  "entitlements": ["premium"],
  "expires_date": "2026-05-19T12:30:00Z",
  "verified_at": "2026-04-19T12:30:00Z"
}
```

#### Check Feature Access

**Endpoint:** `GET /api/subscription/feature/<user_id>/?feature=<feature_name>`

Check if user has access to a specific premium feature.

```bash
curl 'https://api.facesyma.com/api/subscription/feature/123/?feature=unlimited_checks'

# Response:
{
  "feature": "unlimited_checks",
  "has_access": true,
  "plan": "premium",
  "upgrade_required": false
}
```

**Available Features:**

Free tier:
- `compatibility_check_1_per_day`
- `community_browse`
- `profile_view`

Premium tier (everything above + these):
- `unlimited_checks`
- `unlimited_communities`
- `file_sharing`
- `advanced_search`
- `priority_support`
- `meal_game_access` (Phase 6)
- `social_challenges` (Phase 6)
- `custom_badges` (Phase 6)

#### Cancel Subscription

**Endpoint:** `POST /api/subscription/cancel/<user_id>/`

User initiated cancellation (optional). RevenueCat manages subscription cancellation via App Store/Play Store.

```bash
curl -X POST https://api.facesyma.com/api/subscription/cancel/123/

# Response:
{
  "success": true,
  "message": "Subscription cancelled",
  "plan": "free"
}
```

### 3. Protecting Premium Features

#### Option A: Check at API Endpoint

```python
# In any view that requires premium access
from admin_api.views.subscription_views import FeatureAccessView

@method_decorator(csrf_exempt, name='dispatch')
class MealGameView(View):
    def get(self, request, user_id):
        # Check feature access first
        feature_check = FeatureAccessView().get(
            request, user_id
        )
        feature_data = json.loads(feature_check.content)
        
        if feature_data['feature'] != 'meal_game_access':
            return JsonResponse(
                {'detail': 'Premium feature. Please upgrade.'},
                status=403
            )
        
        # Continue with meal game logic
        # ...
```

#### Option B: Middleware Check

```python
# admin_api/middleware/subscription_middleware.py
class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if accessing premium endpoint
        if request.path.startswith('/api/meals/') or \
           request.path.startswith('/api/challenges/'):
            # Attach subscription status to request
            user_id = extract_user_id(request)
            request.subscription = get_subscription_status(user_id)
        
        response = self.get_response(request)
        return response
```

#### Option C: Frontend Check (Recommended for UX)

```javascript
// Check before showing feature
const canAccessMealGame = async (userID) => {
  const response = await fetch(
    `https://api.facesyma.com/api/subscription/feature/${userID}/?feature=meal_game_access`
  );
  const data = await response.json();
  return data.has_access;
};

// In component
if (await canAccessMealGame(userID)) {
  // Show meal game
} else {
  // Show paywall
}
```

## Pricing Strategy

### Global 5-Tier PPP Model

Based on purchasing power parity (PPP), users in different regions get different pricing:

| Tier | Regions | Monthly | Yearly |
|------|---------|---------|--------|
| A | China, India, SE Asia, Latam (low) | $0.99 | $8.99 |
| B | Middle East, Eastern Europe, Latam | $1.99 | $14.99 |
| C | Japan, Korea, Taiwan, Mexico, Brazil | $4.99 | $39.99 |
| D | USA, Canada, Australia, Scandinavia | $12.99 | $99.99 |
| E | Germany, France, UK, Switzerland | €7.99 | €79.99 |

**RevenueCat automatically applies the correct pricing based on user's country.**

### No Backend Price Configuration Needed

RevenueCat handles all regional pricing automatically through App Store Connect and Google Play Console. You just set up the subscription products once, and RevenueCat fetches the correct localized prices.

## Monitoring Subscriptions

### Check Subscription Status in Admin Dashboard

```python
# admin_api/views.py (or add to existing stats endpoint)
from pymongo import MongoClient
from django.conf import settings

def get_subscription_metrics():
    client = MongoClient(settings.MONGO_URI)
    db = client['facesyma-backend']
    
    subscriptions = db['user_subscriptions']
    
    return {
        'total_premium': subscriptions.count_documents({'plan': 'premium'}),
        'total_free': subscriptions.count_documents({'plan': 'free'}),
        'active_subscriptions': subscriptions.count_documents({
            'plan': 'premium',
            'expires_date': {'$gt': datetime.now().isoformat()}
        }),
        'upcoming_renewals': subscriptions.count_documents({
            'plan': 'premium',
            'expires_date': {
                '$gt': datetime.now().isoformat(),
                '$lt': (datetime.now() + timedelta(days=7)).isoformat()
            }
        }),
    }
```

### Database Queries

```bash
# Count premium users
db.user_subscriptions.countDocuments({ plan: "premium" })

# Find users with expiring subscriptions (next 7 days)
db.user_subscriptions.find({
  expires_date: {
    $gt: new Date(),
    $lt: new Date(Date.now() + 7*24*60*60*1000)
  }
})

# Find failed renewals
db.user_subscriptions.find({ payment_status: "failed" })
```

## Testing Subscription Flow

### Local Testing (Development)

1. **Configure RevenueCat Test Credentials**
   ```python
   # settings.py
   REVENUECAT_API_KEY = 'sk_test_xxxxx'  # Test API key
   ```

2. **Test Receipt**
   ```python
   # Use RevenueCat sandbox test receipts
   SANDBOX_FETCH_TOKEN = 'rc_test_token_123'
   ```

3. **Test Endpoints**
   ```bash
   # Verify test subscription
   curl -X POST http://localhost:8000/api/subscription/verify/ \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 999,
       "fetch_token": "rc_test_token_123",
       "is_ios": true
     }'
   
   # Check status
   curl http://localhost:8000/api/subscription/status/999/
   ```

### Production Testing

1. Use TestFlight (iOS) or Google Play Beta (Android)
2. Make real purchases with test credit card
3. Verify receipt in backend
4. Check MongoDB for updated subscription

## Future Payment Integrations

When ready to add more payment methods:

1. **Papara E-Wallet** (Turkish users)
   - Implement `PaparaPaymentGateway` class
   - Create endpoint for wallet-based purchases
   - Setup webhook for payment confirmation

2. **Cryptocurrency**
   - Implement `CoinbaseCommerceGateway` class
   - Create crypto payment address generation
   - Monitor blockchain for confirmations

3. **Stripe** (Web payments)
   - Implement `StripePaymentGateway` class
   - Create web checkout flow
   - Setup webhook for payment notifications

See `PAYMENT_ARCHITECTURE.md` for implementation details.

## Troubleshooting

### Receipt Verification Failed

```
Error: "Receipt verification failed"
```

**Causes:**
- Invalid RevenueCat API key
- Receipt already claimed by another account
- Test receipt used in production

**Solution:**
- Check `REVENUECAT_API_KEY` in environment
- Restore purchases in app
- Use test keys for testing only

### User Plan Not Updating

```
Query: User subscribed but plan still shows "free"
```

**Causes:**
- Frontend didn't call `POST /api/subscription/verify/`
- MongoDB subscription collection not updated

**Solution:**
1. Check mobile app calls verify endpoint after purchase
2. Manually verify subscription:
   ```bash
   curl -X POST http://localhost:8000/api/subscription/verify/ \
     -H "Content-Type: application/json" \
     -d '{"user_id": 123, "fetch_token": "...", "is_ios": true}'
   ```

### Feature Access Check Failing

```
Error: "Feature access not found"
```

**Solution:**
- Ensure user has valid subscription
- Check spelling of feature name
- Verify feature exists in `premium_features` list

## Support

For payment-related issues:
- **RevenueCat Docs:** https://docs.revenuecat.com
- **App Store Docs:** https://developer.apple.com/in-app-purchase/
- **Google Play Docs:** https://developer.android.com/google/play/billing
