# App Store Connect - Subscription Setup Guide

## Overview

App Store Connect subscription products for Facesyma Premium across 5 global pricing tiers using RevenueCat.

## Prerequisites

✅ Apple Developer Account ($99/year)
✅ App ID created in App Store Connect
✅ Bundle ID: `com.facesyma.app`
✅ iOS app uploaded with RevenueCat SDK integrated

## Step 1: Create Subscription Group

**Location:** App Store Connect → Your App → In-App Purchases

### Name Subscription Group
- **Group Name:** `facesyma_premium_subscription`
- **Reference Name:** Premium Subscription
- **This will contain all Tier A-E subscription products**

## Step 2: Create Subscription Products (5 Tiers)

### Tier A: Emerging Markets (China, India, SE Asia)

#### Monthly - Tier A
```
Product ID: com.facesyma.premium.monthly.tier_a
Reference Name: Premium Monthly (Tier A)
Subscription Group: facesyma_premium_subscription

Localized Info:
  Display Name: Premium Monthly
  Description: Unlimited face analysis, advanced search, priority support

Pricing:
  Annual Renewable Subscription

Auto-Renewable Subscription Details:
  Duration: 1 Month
  Free Trial: 7 Days (optional - recommended for first purchase)
```

**Regional Pricing for Tier A:**
```
China (CNY):              ¥6.99 (≈ $0.99 USD equivalent)
India (INR):             ₹79 (≈ $0.95 USD)
Thailand (THB):          ฿39 (≈ $1.10 USD)
Vietnam (VND):           ₫24,000 (≈ $1.00 USD)
Philippines (PHP):       ₱59 (≈ $1.06 USD)
Indonesia (IDR):         Rp15,000 (≈ $0.95 USD)
Bangladesh (BDT):        ৳99 (≈ $1.18 USD)
Pakistan (PKR):          ₨149 (≈ $0.53 USD)
```

#### Yearly - Tier A
```
Product ID: com.facesyma.premium.yearly.tier_a
Reference Name: Premium Yearly (Tier A)
Subscription Group: facesyma_premium_subscription

Auto-Renewable Subscription Details:
  Duration: 12 Months
  Free Trial: 7 Days
```

**Regional Pricing for Tier A (Yearly - 15% discount):**
```
China (CNY):              ¥59.99 (≈ $8.99 USD)
India (INR):             ₹679 (≈ $8.16 USD)
Thailand (THB):          ฿329 (≈ $9.34 USD)
Vietnam (VND):           ₫204,000 (≈ $8.50 USD)
Philippines (PHP):       ₱499 (≈ $8.99 USD)
Indonesia (IDR):         Rp127,500 (≈ $8.09 USD)
```

### Tier B: Developing Economies (Middle East, Eastern Europe)

#### Monthly - Tier B
```
Product ID: com.facesyma.premium.monthly.tier_b
Reference Name: Premium Monthly (Tier B)

Pricing Table:
Saudi Arabia (SAR):      ر.س 7.99 (≈ $2.13 USD)
UAE (AED):              د.إ 7.99 (≈ $2.17 USD)
Egypt (EGP):            ج.م 59 (≈ $1.95 USD)
Turkey (TRY):           ₺39.99 (≈ $1.34 USD)
Poland (PLN):           zł7.99 (≈ $2.02 USD)
Czech Republic (CZK):   Kč49.99 (≈ $2.13 USD)
Hungary (HUF):          Ft749 (≈ $2.06 USD)
Romania (RON):          lei 9.99 (≈ $2.14 USD)
```

#### Yearly - Tier B
```
Product ID: com.facesyma.premium.yearly.tier_b
Yearly with 15% discount:

Saudi Arabia (SAR):      ر.س 67.99 (≈ $18.13 USD)
UAE (AED):              د.إ 67.99 (≈ $18.52 USD)
Egypt (EGP):            ج.م 499 (≈ $16.58 USD)
Turkey (TRY):           ₺339.99 (≈ $11.39 USD)
```

### Tier C: Growing Markets (Japan, Korea, Brazil, Mexico)

#### Monthly - Tier C
```
Product ID: com.facesyma.premium.monthly.tier_c
Reference Name: Premium Monthly (Tier C)

Japan (JPY):            ¥590 (≈ $4.03 USD)
South Korea (KRW):      ₩5,900 (≈ $4.45 USD)
Brazil (BRL):           R$ 24.99 (≈ $5.08 USD)
Mexico (MXN):           $ 99.99 (≈ $5.88 USD)
Argentina (ARS):        $ 1,299 (≈ $4.31 USD)
Colombia (COP):         $ 19,900 (≈ $4.97 USD)
```

#### Yearly - Tier C
```
Product ID: com.facesyma.premium.yearly.tier_c
Yearly with 15% discount:

Japan (JPY):            ¥4,990 (≈ $34.25 USD)
South Korea (KRW):      ₩49,900 (≈ $37.83 USD)
Brazil (BRL):           R$ 212.49 (≈ $43.18 USD)
Mexico (MXN):           $ 849.99 (≈ $49.94 USD)
```

### Tier D: Developed Nations (USA, Canada, Australia)

#### Monthly - Tier D
```
Product ID: com.facesyma.premium.monthly.tier_d
Reference Name: Premium Monthly (Tier D)

United States (USD):    $12.99
Canada (CAD):           C$18.99 (≈ $13.96 USD)
Australia (AUD):        A$21.49 (≈ $14.36 USD)
New Zealand (NZD):      NZ$24.99 (≈ $15.23 USD)
```

#### Yearly - Tier D
```
Product ID: com.facesyma.premium.yearly.tier_d
Yearly with 15% discount:

United States (USD):    $99.99
Canada (CAD):           C$149.99 (≈ $110.13 USD)
Australia (AUD):        A$169.99 (≈ $113.75 USD)
New Zealand (NZD):      NZ$199.99 (≈ $122.06 USD)
```

### Tier E: Premium Markets (Germany, France, UK, EU)

#### Monthly - Tier E
```
Product ID: com.facesyma.premium.monthly.tier_e
Reference Name: Premium Monthly (Tier E)

Euro Zone (EUR):        €7.99
United Kingdom (GBP):   £7.99 (≈ $9.99 USD)
Switzerland (CHF):      CHF 12.99 (≈ $14.72 USD)
Denmark (DKK):          kr 59.99 (≈ $8.05 USD)
Sweden (SEK):           kr 89.99 (≈ $8.60 USD)
Norway (NOK):           kr 99.99 (≈ $9.54 USD)
```

#### Yearly - Tier E
```
Product ID: com.facesyma.premium.yearly.tier_e
Yearly with 15% discount:

Euro Zone (EUR):        €67.99
United Kingdom (GBP):   £67.99 (≈ $85.16 USD)
Switzerland (CHF):      CHF 109.99 (≈ $124.83 USD)
Denmark (DKK):          kr 509.99 (≈ $68.38 USD)
Sweden (SEK):           kr 764.99 (≈ $73.00 USD)
Norway (NOK):           kr 849.99 (≈ $81.06 USD)
```

## Step 3: Configure Subscription Settings

### In-App Purchase Details (for each product)

```
✓ Managed by RevenueCat (external entitlement provider)

Reference Name:        Premium Monthly Tier A
Product ID:            com.facesyma.premium.monthly.tier_a
Type:                  Auto-Renewable Subscription
Status:                Ready to Submit

Subscription Information:
  Group:               facesyma_premium_subscription
  Duration:            1 Month
  Free Trial Period:    7 Days
  Billing Grace Period: 3 Days (allows payment retry)
  
Subscription Intro Offer (Optional):
  Intro Price:         $0.99 for 7 days (as free trial)
  OR: $0.99 for 1 month (first month discount)

Availability:
  ✓ Add this subscription to the current version
  ✓ Check all regions
```

### Entitlements (for RevenueCat)

```
Entitlement ID:        premium
Entitlement Name:      Premium Access

Products:
  ✓ com.facesyma.premium.monthly.tier_a
  ✓ com.facesyma.premium.yearly.tier_a
  ✓ com.facesyma.premium.monthly.tier_b
  ✓ com.facesyma.premium.yearly.tier_b
  ✓ com.facesyma.premium.monthly.tier_c
  ✓ com.facesyma.premium.yearly.tier_c
  ✓ com.facesyma.premium.monthly.tier_d
  ✓ com.facesyma.premium.yearly.tier_d
  ✓ com.facesyma.premium.monthly.tier_e
  ✓ com.facesyma.premium.yearly.tier_e
```

## Step 4: Configure RevenueCat Integration

### In App Store Connect

1. **Enable Server-to-Server Notifications**
   - Location: Your App → App Store Server Notifications
   - URL: `https://api.revenuecat.com/applewebhook/[YOUR_API_KEY]`
   - Request Version: 2 (newest)
   - Enable: ✓ All subscription events
   - Enable: ✓ Refund events

2. **Get App Store Server Signing Key**
   - Location: Your App → In-App Purchases
   - Click: "Issues" tab → "Configure" for App Store Server API
   - Create Key: Select "In-App Purchase" key type
   - Download: `AuthKey_XXXXXXXXXX.p8` file
   - **Save this file securely**

### In RevenueCat Dashboard

1. Go to: https://dashboard.revenuecat.com
2. Select: Projects → Your Project → iOS App
3. Section: "App Store Server API"
   - Private Key: Upload the `.p8` file
   - Key ID: `XXXXXXXXXX`
   - Issuer ID: (visible in App Store Connect → Users and Access → Certificates, Identifiers & Profiles)
4. Click: Save

## Step 5: Screenshot & Metadata (App Review)

### Subscription Display Name
```
Display Name (shown in App Store):
  "Premium - Unlimited Face Analysis"

Description (shown in receipt):
  "Access unlimited face compatibility checks, 
   advanced search features, priority customer support, 
   meal game access, and social challenges."
```

### Preview Text (for App Store listing)
```
"Enjoy unlimited face analysis, advanced features, 
and priority support with Premium."
```

## Step 6: Prepare for TestFlight

### Create TestFlight Test Account

1. Users and Access → Sandbox Testers → Create
   ```
   Email: test-ios@facesyma.com
   Password: (secure password)
   Name: iOS Test Account
   ```

2. Invite to TestFlight
   - App Store Connect → TestFlight → Internal Testing
   - Add test account
   - User will receive email with TestFlight beta link

### Testing Subscription Purchase

```bash
# On iOS TestFlight App
1. Launch Facesyma Beta
2. Navigate to Upgrade/Premium screen
3. Tap on Monthly or Yearly subscription
4. Confirm purchase
5. Use Sandbox payment (no real charge)
   - Name: Test
   - Card: 4111111111111111
   - Expiry: 01/25
   - CVV: 123
6. Verify receipt synced to backend
   - Backend shows: plan = "premium"
   - Subscription status: active
   - Feature access: unlimited_checks = true
```

## Step 7: Submit App Update to App Review

1. Build new app version with RevenueCat SDK
2. Version: 1.1.0 (or next version)
3. Build #: Auto-incremented
4. TestFlight Internal Testing: PASS ✓
5. Submit for Review

### Review Information

```
Subscription Information:
  Tier A (Emerging): $0.99/month, $8.99/year
  Tier B (Developing): $1.99/month, $14.99/year
  Tier C (Growing): $4.99/month, $39.99/year
  Tier D (Developed): $12.99/month, $99.99/year
  Tier E (Premium): €7.99/month, €79.99/year

Free Trial: 7 days (if enabled)
Renewal: Automatic, user can manage in Settings

Will be managed by RevenueCat (external provider)
```

## Step 8: Monitor Launch & Analytics

### Daily Checks Post-Launch

```bash
# In App Store Connect → Analytics
- Overall Sales
- In-App Purchases Revenue
- Subscription Conversion Rate
- Churn Rate (monthly)
- Retention Cohorts

# In RevenueCat Dashboard
- Active Subscriptions by Tier
- Monthly Recurring Revenue (MRR)
- Conversion Funnel
- Churn Analysis
- Refund Rate
```

## Pricing Table Summary

### All Product IDs Created

```
TIER A (Emerging Markets)
├── Monthly: com.facesyma.premium.monthly.tier_a ($0.99)
└── Yearly:  com.facesyma.premium.yearly.tier_a ($8.99)

TIER B (Developing Economies)
├── Monthly: com.facesyma.premium.monthly.tier_b ($1.99)
└── Yearly:  com.facesyma.premium.yearly.tier_b ($14.99)

TIER C (Growing Markets)
├── Monthly: com.facesyma.premium.monthly.tier_c ($4.99)
└── Yearly:  com.facesyma.premium.yearly.tier_c ($39.99)

TIER D (Developed Nations)
├── Monthly: com.facesyma.premium.monthly.tier_d ($12.99)
└── Yearly:  com.facesyma.premium.yearly.tier_d ($99.99)

TIER E (Premium Markets)
├── Monthly: com.facesyma.premium.monthly.tier_e (€7.99)
└── Yearly:  com.facesyma.premium.yearly.tier_e (€79.99)

ENTITLEMENT: premium
```

## Post-Setup Verification Checklist

- [ ] All 10 products created in App Store Connect
- [ ] All regional prices configured correctly
- [ ] Subscription Group created: `facesyma_premium_subscription`
- [ ] Entitlement linked: `premium`
- [ ] Server-to-Server notifications enabled
- [ ] App Store Server API key configured in RevenueCat
- [ ] TestFlight test account created
- [ ] Test purchase flow verified (no errors)
- [ ] Backend receives subscription verification
- [ ] User plan updates to "premium" in MongoDB
- [ ] Feature access grants premium features
- [ ] App submitted to App Review with subscription details

## Troubleshooting

### Products Not Appearing in App
```
Issue: User doesn't see subscription options
Cause: App not updated with RevenueCat SDK
Fix: 
  1. Ensure PurchaseService.js is initialized
  2. Call getSubscriptionPackages() after login
  3. Check RevenueCat API key is correct
  4. Verify products are Live (not Draft)
```

### Wrong Price Displays
```
Issue: User sees $0.99 instead of regional price
Cause: RevenueCat hasn't synced pricing yet
Fix:
  1. Wait 15-30 minutes for sync
  2. Verify prices in App Store Connect
  3. Check user's App Store region
  4. Clear app cache and restart
```

### Test Purchase Fails
```
Issue: "Unable to connect to App Store" error
Cause: Using real App Store instead of Sandbox
Fix:
  1. Use TestFlight beta for testing
  2. Configure Sandbox credentials
  3. Verify Bundle ID matches
  4. Check internet connectivity
```

## Next Steps

1. ✅ Create all 10 subscription products
2. ✅ Configure regional pricing
3. ✅ Setup RevenueCat integration
4. → Submit app to App Review
5. → Launch on App Store
6. → Monitor analytics in RevenueCat Dashboard

See also: `GOOGLE_PLAY_CONSOLE_SETUP.md` for Android setup
