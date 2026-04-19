# Google Play Console - Subscription Setup Guide

## Overview

Google Play subscription products for Facesyma Premium across 5 global pricing tiers using RevenueCat.

## Prerequisites

✅ Google Play Developer Account ($25 one-time)
✅ Android app Bundle ID: `com.facesyma.app`
✅ Signed APK/AAB uploaded to Play Console
✅ RevenueCat SDK integrated in app

## Step 1: Create Subscription Base Plans

**Location:** Google Play Console → Your App → Manage Products → Subscriptions

### Name Your Subscription Base Plan

```
Base Plan ID: tier_a_monthly
Display Name: Premium Monthly (Tier A)
Billing Period: Monthly (1 month)
Grace Period: 3 days (for payment retry)
Account Hold Period: 30 days
```

**Repeat for all 5 tiers:**

```
Tier A:
  ├── tier_a_monthly (1 month)
  └── tier_a_yearly (12 months)

Tier B:
  ├── tier_b_monthly (1 month)
  └── tier_b_yearly (12 months)

Tier C:
  ├── tier_c_monthly (1 month)
  └── tier_c_yearly (12 months)

Tier D:
  ├── tier_d_monthly (1 month)
  └── tier_d_yearly (12 months)

Tier E:
  ├── tier_e_monthly (1 month)
  └── tier_e_yearly (12 months)
```

## Step 2: Configure Regional Prices (Tier A)

### Tier A: Emerging Markets

**Base Plan:** tier_a_monthly

#### Monthly Pricing - Tier A

```
Price Setup:
  Default Price: $0.99 USD

Regional Overrides (Auto-converted, but override if needed):
  
China (CNY):              ¥6.99
  └─ Auto: ~$0.96 (based on USD conversion)
  
India (INR):             ₹79
  └─ Auto: ~$0.95
  
Thailand (THB):          ฿39
  └─ Auto: ~$1.10
  
Vietnam (VND):           ₫24,000
  └─ Auto: ~$1.00
  
Philippines (PHP):       ₱59
  └─ Auto: ~$1.06
  
Indonesia (IDR):         Rp15,000
  └─ Auto: ~$0.95
  
Bangladesh (BDT):        ৳99
  └─ Auto: ~$1.18
  
Pakistan (PKR):          ₨149
  └─ Auto: ~$0.53
  
Malaysia (MYR):          RM 4.99
  └─ Auto: ~$1.07
  
Singapore (SGD):         S$ 1.68
  └─ Auto: ~$1.26
  
Sri Lanka (LKR):         Rs 399
  └─ Auto: ~$1.20
```

**How to set in Google Play:**
1. Click "Add currency"
2. Select country
3. Enter price in local currency
4. Save

#### Yearly Pricing - Tier A (15% discount)

```
Base Plan: tier_a_yearly
Default Price: $8.99 USD (15% off from $10.58)

Regional Overrides:
  
China (CNY):              ¥59.99
India (INR):             ₹679
Thailand (THB):          ฿329
Vietnam (VND):           ₫204,000
Philippines (PHP):       ₱499
Indonesia (IDR):         Rp127,500
Bangladesh (BDT):        ৳829
Pakistan (PKR):          ₨1,299
Malaysia (MYR):          RM 42.49
Singapore (SGD):         S$ 14.28
```

## Step 3: Configure Regional Prices (Tier B)

### Tier B: Developing Economies

**Base Plan:** tier_b_monthly

#### Monthly - Tier B

```
Default Price: $1.99 USD

Regional Pricing:

Saudi Arabia (SAR):      ر.س 7.99 (~$2.13)
United Arab Emirates (AED): د.إ 7.99 (~$2.17)
Egypt (EGP):            ج.م 59 (~$1.95)
Turkey (TRY):           ₺39.99 (~$1.34)
Israel (ILS):           ₪7.99 (~$2.16)
Poland (PLN):           zł 7.99 (~$2.02)
Czech Republic (CZK):   Kč 49.99 (~$2.13)
Hungary (HUF):          Ft 749 (~$2.06)
Romania (RON):          lei 9.99 (~$2.14)
South Africa (ZAR):     R 39.99 (~$2.14)
Colombia (COP):         $ 8,000 (~$2.00)
Peru (PEN):             S/ 7.99 (~$2.16)
```

#### Yearly - Tier B (15% discount)

```
Base Plan: tier_b_yearly
Default Price: $14.99 USD

Regional Pricing (15% discount applied):

Saudi Arabia (SAR):      ر.س 67.99
UAE (AED):              د.إ 67.99
Egypt (EGP):            ج.م 499
Turkey (TRY):           ₺339.99
Israel (ILS):           ₪ 67.99
Poland (PLN):           zł 67.99
Czech Republic (CZK):   Kč 424.99
Hungary (HUF):          Ft 6,399
Romania (RON):          lei 84.99
South Africa (ZAR):     R 339.99
```

## Step 4: Configure Regional Prices (Tier C)

### Tier C: Growing Markets

**Base Plan:** tier_c_monthly

#### Monthly - Tier C

```
Default Price: $4.99 USD

Regional Pricing:

Japan (JPY):            ¥ 590
South Korea (KRW):      ₩ 5,900
Brazil (BRL):           R$ 24.99
Mexico (MXN):           $ 99.99
Argentina (ARS):        $ 1,299
Chile (CLP):            $ 4,490
Colombia (COP):         $ 19,900
Costa Rica (CRC):       ₡ 3,099
Panama (PAB):           B/. 4.99
Thailand (THB):         ฿ 189
Malaysia (MYR):         RM 21.99
Vietnam (VND):          ₫ 129,000
Philippines (PHP):      ₱ 249
```

#### Yearly - Tier C (15% discount)

```
Base Plan: tier_c_yearly
Default Price: $39.99 USD

Regional Pricing:

Japan (JPY):            ¥ 4,990
South Korea (KRW):      ₩ 49,900
Brazil (BRL):           R$ 212.49
Mexico (MXN):           $ 849.99
Argentina (ARS):        $ 11,049
Chile (CLP):            $ 38,199
Colombia (COP):         $ 169,199
Costa Rica (CRC):       ₡ 26,399
Thailand (THB):         ฿ 1,609
Malaysia (MYR):         RM 186.99
Vietnam (VND):          ₫ 1,098,000
Philippines (PHP):      ₱ 2,119
```

## Step 5: Configure Regional Prices (Tier D)

### Tier D: Developed Nations

**Base Plan:** tier_d_monthly

#### Monthly - Tier D

```
Default Price: $12.99 USD

Regional Pricing:

United States (USD):    $12.99
Canada (CAD):           C$18.99
Australia (AUD):        A$21.49
New Zealand (NZD):      NZ$24.99
United Kingdom (GBP):   £11.99
Finland (EUR):          €11.99
France (EUR):           €11.99
Germany (EUR):          €11.99
Italy (EUR):            €11.99
Spain (EUR):            €11.99
Netherlands (EUR):      €11.99
Belgium (EUR):          €11.99
Austria (EUR):          €11.99
Portugal (EUR):         €11.99
Greece (EUR):           €11.99
Ireland (EUR):          €11.99
Luxembourg (EUR):       €11.99
Malta (EUR):            €11.99
Cyprus (EUR):           €11.99
Slovenia (EUR):         €11.99
Slovakia (EUR):         €11.99
```

#### Yearly - Tier D (15% discount)

```
Base Plan: tier_d_yearly
Default Price: $99.99 USD

Regional Pricing:

United States (USD):    $99.99
Canada (CAD):           C$149.99
Australia (AUD):        A$169.99
New Zealand (NZD):      NZ$199.99
United Kingdom (GBP):   £99.99
Euro Zone (EUR):        €99.99
```

## Step 6: Configure Regional Prices (Tier E)

### Tier E: Premium Markets

**Base Plan:** tier_e_monthly

#### Monthly - Tier E

```
Default Price: €7.99 EUR

Regional Pricing:

Euro Zone (EUR):        €7.99
  (Austria, Belgium, Cyprus, Estonia, Finland,
   France, Germany, Greece, Ireland, Italy,
   Latvia, Lithuania, Luxembourg, Malta,
   Netherlands, Portugal, Slovakia, Slovenia, Spain)

United Kingdom (GBP):   £7.99 (~$9.99 USD)
Switzerland (CHF):      CHF 12.99 (~$14.72 USD)
Denmark (DKK):          kr 59.99 (~$8.05 USD)
Sweden (SEK):           kr 89.99 (~$8.60 USD)
Norway (NOK):           kr 99.99 (~$9.54 USD)
Iceland (ISK):          kr 1,299 (~$9.83 USD)
```

#### Yearly - Tier E (15% discount)

```
Base Plan: tier_e_yearly
Default Price: €67.99 EUR

Regional Pricing:

Euro Zone (EUR):        €67.99
United Kingdom (GBP):   £67.99
Switzerland (CHF):      CHF 109.99
Denmark (DKK):          kr 509.99
Sweden (SEK):           kr 764.99
Norway (NOK):           kr 849.99
Iceland (ISK):          kr 11,049
```

## Step 7: Configure Intro Offers (Optional but Recommended)

### Free Trial Offer

For each base plan, optionally add:

```
Intro Offer Type: Free Trial
Duration: 7 days
Billing Period: (none - completely free)
Auto-renews to: Full price after 7 days
```

**Enable for:**
- All Tier A plans
- All Tier B plans
- Tier C - optional (consider for conversion)

### Alternative: Discounted First Month

```
Intro Offer Type: Discounted Price
Duration: First Billing Period (1 month)
Price: $0.99 (pay once, then auto-renew at full price)
Auto-renews to: Full price
```

**Only if different from free trial approach**

## Step 8: Configure Subscription Descriptions

### Localized Descriptions

**English:**
```
Title: Premium - Unlimited Face Analysis

Description:
Get unlimited face compatibility analysis, advanced search,
priority customer support, exclusive gamification features,
and access to our AI coaching modules.

Features:
• Unlimited face compatibility checks
• Advanced search and filters
• Priority customer support
• Meal game access with leaderboards
• Social challenges and achievements
• Custom personality profiles
• AI relationship coach
```

**Repeat for:**
- Turkish (Türkçe)
- Chinese Simplified (简体中文)
- Chinese Traditional (繁體中文)
- Korean (한국어)
- Japanese (日本語)
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Portuguese (Português)
- Russian (Русский)
- Arabic (العربية)
- Hindi (हिन्दी)
- Thai (ไทย)
- Vietnamese (Tiếng Việt)
- Polish (Polski)
- Italian (Italiano)
- Hebrew (עברית)

## Step 9: Configure Play Billing Integration

### In Google Play Console

1. **Merchant Account Setup**
   - Location: Setup → Account Details
   - Verify: Merchant account is active
   - Payment methods: Credit card, Google Pay accepted

2. **Revenue Sharing Agreement**
   - Google Play keeps 30%
   - Developer gets 70%
   - (Standard for all subscriptions)

### In RevenueCat Dashboard

1. Go to: https://dashboard.revenuecat.com
2. Select: Projects → Your Project → Android App
3. Section: "Google Play Service Account"
   - Create Service Account in Google Play Console:
     - Settings → Service Accounts → Create Service Account
     - Download JSON credentials file
   - Upload JSON to RevenueCat
   - Service Account email: (auto-filled)

4. **Configure Pub/Sub Webhook**
   - Create Topic: `projects/[PROJECT-ID]/topics/revenuecat-webhook`
   - Create Subscription: Create Push Subscription
   - Push Endpoint: `https://api.revenuecat.com/googlewebhook/[YOUR_API_KEY]`
   - Click Create

## Step 10: Testing Configuration

### Create Test Account

1. **Create Google Play Account for Testing**
   - Use different Gmail account
   - Add as License Tester: Settings → License Testing
   ```
   Gmail: test-android@facesyma.com
   ```

2. **Create Google Wallet Test Account**
   - Not needed for in-app testing (automatic)

3. **Install Build on Test Device**
   ```bash
   adb install -r app-release.aab
   ```

4. **Test Purchase Flow**
   ```
   1. Open app
   2. Login with test account
   3. Navigate to Premium screen
   4. Click "Monthly" subscription
   5. Google Play payment prompt appears
   6. Tap "Buy"
   7. Payment reserved (no charge on test account)
   8. Receipt synced to backend
   9. Verify: plan = "premium" in MongoDB
   10. Verify: features unlock
   ```

### Test Error Scenarios

```
Test Case: Invalid Payment Method
  → Ensure 7-day grace period handles retries
  → Backend shows: payment_status = "pending"

Test Case: User Cancels Purchase
  → App handles: user_cancelled error
  → Show: "Purchase cancelled" message

Test Case: Subscription Expires
  → Backend automatically downgrades to free
  → User receives renewal reminder notification

Test Case: User Restores Purchase
  → User taps "Restore" button
  → Receipt synced
  → Features restored within 10 seconds
```

## Step 11: Staged Rollout (Recommended)

### Phased Approach

```
Phase 1: Internal Testing (1 week)
  ├─ 100% of testers on internal testing track
  ├─ Verify all regions, all pricing tiers
  ├─ Confirm backend syncs correctly
  └─ Fix any issues

Phase 2: Closed Beta (2 weeks)
  ├─ 25% of users (if you have beta program)
  ├─ Real devices, real network conditions
  ├─ Collect feedback from real purchases
  └─ Monitor crash reports

Phase 3: Public Release (gradual)
  ├─ Day 1: 10% of users
  ├─ Day 3: 25% of users
  ├─ Day 7: 100% of users
  └─ Monitor revenue and errors at each phase
```

**How to set in Google Play Console:**
1. Release Management → Releases → Create Release
2. Select testing track (internal → closed → production)
3. Set percentage rollout: 10% → 25% → 100%

## Step 12: Submission & Review

### App Review Information

```
Subscription Details:
  Tier A (Emerging): $0.99/month, $8.99/year
  Tier B (Developing): $1.99/month, $14.99/year
  Tier C (Growing): $4.99/month, $39.99/year
  Tier D (Developed): $12.99/month, $99.99/year
  Tier E (Premium): €7.99/month, €79.99/year

Free Trial: 7 days (first purchase only)
Renewal: Automatic, user can cancel in Google Play
Cancellation: Users can cancel in Play Store Settings
```

### Privacy Policy Update

Add to your privacy policy:

```
## In-App Purchases & Subscriptions

Facesyma offers optional subscription plans through Google Play.

- Subscriptions auto-renew monthly or yearly
- Charges appear on your Google Play billing
- You can cancel any time via Google Play Settings
- No refund after first 7 days (except if laws require)
- Prices vary by country and may change
- Your subscription is managed by RevenueCat
```

## Post-Launch Monitoring

### Key Metrics to Track

```
Google Play Console → Analytics:
  ├─ Subscription Revenue
  ├─ New Subscribers by Tier
  ├─ Churn Rate
  ├─ Retention Cohorts
  ├─ Refund Rate
  └─ Revenue per Paying User

RevenueCat Dashboard:
  ├─ Active Subscriptions
  ├─ Monthly Recurring Revenue (MRR)
  ├─ Conversion Funnel
  ├─ Lifetime Value (LTV)
  ├─ Cohort Analysis
  └─ Revenue by Tier
```

### Alerts to Configure

```
Create Alerts for:
1. Sudden drop in conversion rate (>10%)
2. Churn spike (>5% weekly)
3. Refund rate increases (>2%)
4. Backend subscription sync failures
5. Missing revenue data (sync delays)
```

## Pricing Summary

### All Subscription Base Plans Created

```
TIER A (Emerging Markets - $0.99/$8.99)
├── tier_a_monthly
└── tier_a_yearly

TIER B (Developing - $1.99/$14.99)
├── tier_b_monthly
└── tier_b_yearly

TIER C (Growing - $4.99/$39.99)
├── tier_c_monthly
└── tier_c_yearly

TIER D (Developed - $12.99/$99.99)
├── tier_d_monthly
└── tier_d_yearly

TIER E (Premium - €7.99/€79.99)
├── tier_e_monthly
└── tier_e_yearly
```

## Setup Verification Checklist

- [ ] All 10 base plans created
- [ ] Regional prices configured for all regions
- [ ] Free trial offer enabled (7 days)
- [ ] Localized descriptions created (18 languages)
- [ ] Subscription product icons uploaded
- [ ] Service Account configured in RevenueCat
- [ ] Pub/Sub webhook configured
- [ ] Test account created for testing
- [ ] Internal testing phase: PASS ✓
- [ ] All pricing displays correctly
- [ ] Backend receives purchases via webhook
- [ ] User plan updates to "premium"
- [ ] Feature access grants premium features
- [ ] Cancellation works correctly
- [ ] App submitted for review

## Troubleshooting

### "Billing library not available" Error

```
Issue: User sees this error on device
Cause: Google Play Services not up to date
Fix:
  1. Ensure android:minSdkVersion = "21"
  2. Update Google Play Services
  3. Test on device with Play Store app
```

### Purchases Not Syncing to Backend

```
Issue: User purchases but plan stays "free"
Cause: Pub/Sub webhook not configured
Fix:
  1. Verify Service Account has correct permissions
  2. Check webhook URL in RevenueCat
  3. Look for errors in RevenueCat Logs
  4. Check backend receives POST requests
```

### Regional Price Not Showing

```
Issue: User in Japan sees USD price
Cause: Price not set for country's currency
Fix:
  1. Add currency override for JPY
  2. Wait 15-30 minutes for sync
  3. Clear Play Store app cache
  4. Force stop and restart app
```

### High Refund Rate

```
Issue: More than 2% refunds
Cause: Could be free trial abuse or payment issues
Fix:
  1. Review refund reasons in Play Console
  2. Check for payment failures
  3. Ensure paywall copy is clear
  4. Consider improving free trial → conversion
```

## Next Steps

1. ✅ Create all 10 subscription base plans
2. ✅ Configure regional pricing
3. ✅ Setup RevenueCat integration
4. → Test with internal testing track
5. → Staged rollout (10% → 25% → 100%)
6. → Monitor metrics & adjust as needed

See also: `APP_STORE_CONNECT_SETUP.md` for iOS setup
