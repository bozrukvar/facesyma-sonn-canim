# Mobile End-to-End Testing Guide - Subscription Flow

## Overview

Complete testing guide for Facesyma subscription system across iOS and Android platforms.

## Prerequisites

### iOS Testing
- ✅ Xcode 14+
- ✅ iPhone/iPad with iOS 14+
- ✅ Apple TestFlight access
- ✅ Sandbox Test Account created in App Store Connect
- ✅ Facesyma Beta app installed via TestFlight

### Android Testing
- ✅ Android Studio 4.1+
- ✅ Android device with Android 6.0+
- ✅ Google Play Services installed
- ✅ Google Play Store app (any version)
- ✅ Google Play License Tester account
- ✅ Facesyma Beta app installed from Google Play

## Test Environment Setup

### iOS - Create Sandbox Test Account

**In App Store Connect:**

1. Users and Access → Sandbox Testers → Create
```
Email: test-ios-1@example.com
Password: TestPassword123!@
Name: iOS Test User
Date of Birth: 01/01/1990
```

2. Accept: Review license agreement in email

3. Logout from iOS App
   - Settings → [Your App] → Sign Out

4. Use Sandbox Account
   - In app: Try to purchase
   - iOS will show: "You're using sandbox mode"

### Android - Add License Tester

**In Google Play Console:**

1. Settings → License Testing
```
Tester Gmail: test-android-1@gmail.com
Account Type: License Tester
```

2. Logout from device
   - Settings → Accounts → Google → Remove account
   - Re-login with test account

## Test Cases

### Test Case 1: App Initialization & RevenueCat SDK

**Goal:** Verify RevenueCat initializes correctly

**iOS Steps:**
```
1. Install app from TestFlight
2. Open app (first launch)
3. Observe console: "✅ RevenueCat initialized"
4. Click any button (to trigger initialization)
5. Check: No "RevenueCat init error" messages
```

**Android Steps:**
```
1. Install app from Play Store (Beta track)
2. Open app (first launch)
3. Monitor logs: adb logcat | grep RevenueCat
4. Expect: "RevenueCat initialized"
5. Verify: Google Play Services responds
```

**Expected Result:** ✅
```
- App initializes RevenueCat SDK
- No errors in console
- Network request to RevenueCat completes
```

**Failure Scenarios:**
```
❌ RevenueCat API key not set
   → Check: REVENUECAT_API_KEY in environment

❌ "Unable to connect to RevenueCat"
   → Check: Network connectivity
   → Check: API key is valid for staging/production

❌ SDK initialization timeout
   → Check: Internet connection is stable
   → Check: Firewall not blocking api.revenuecat.com
```

### Test Case 2: User Login & Identity Setup

**Goal:** Verify RevenueCat user ID synced after login

**iOS Steps:**
```
1. Tap "Sign In" button
2. Enter email: test-ios-1@example.com
3. Enter password: (correct password)
4. Tap "Login"
5. Wait for authentication (5-10 seconds)
6. Observe console: "✅ RevenueCat user set: 123"
```

**Android Steps:**
```
1. Tap "Sign In" button
2. Enter test account email
3. Enter password
4. Tap "Login"
5. adb logcat | grep "RevenueCat user set"
6. Expect: "✅ RevenueCat user set: [user_id]"
```

**Expected Result:** ✅
```
- User successfully authenticates
- Backend returns user ID (e.g., 123)
- RevenueCat user ID updated
- Subscription status fetched (shows "free" initially)
```

**Failure Scenarios:**
```
❌ "Invalid credentials"
   → Verify: Email/password correct
   → Verify: User account exists in MongoDB

❌ Login timeout after 30 seconds
   → Check: Backend server is running
   → Check: Internet connection

❌ RevenueCat user set fails silently
   → Check: User ID is valid integer
   → Check: RevenueCat service account configured
```

### Test Case 3: Get Available Subscription Packages

**Goal:** Verify subscription packages display with correct pricing

**iOS Steps:**
```
1. After login, navigate to Premium/Upgrade screen
2. Wait for packages to load
3. Observe packages displayed:
   ✓ Monthly subscription (auto-localized price)
   ✓ Yearly subscription (auto-localized price)
   ✓ Currency symbol matches device region
   ✓ Trial badge shows "7-Day Free Trial"

Example output (for US user):
  Premium Monthly: $12.99 / month
  Premium Yearly: $99.99 / year
  
Example output (for Japan user):
  Premium Monthly: ¥590 / month
  Premium Yearly: ¥4,990 / year
```

**Android Steps:**
```
1. After login, tap "Upgrade Premium"
2. Wait for packages to load (2-3 seconds)
3. Verify display:
   ✓ "Premium Monthly - $12.99"
   ✓ "Premium Yearly - $99.99"
   ✓ "Save 15% with yearly" text
   ✓ Buttons: "Subscribe" + "Restore"
```

**Expected Result:** ✅
```
- Packages load within 3 seconds
- Prices match region and currency
- Trial period shows (if enabled)
- All CTAs are tappable
```

**Failure Scenarios:**
```
❌ Packages never load (spinner forever)
   → Check: getSubscriptionPackages() returns data
   → Check: RevenueCat offerings configured
   → Check: Network connectivity

❌ Wrong price displayed (e.g., USD instead of JPY)
   → Check: Device region settings
   → Check: App Store/Play Store account region
   → Check: RevenueCat pricing synced

❌ Trial badge not showing
   → Check: Free trial enabled in App Store/Play
   → Check: RevenueCat offerings include intro offer
   → Check: User eligible for trial (first subscription)
```

### Test Case 4: Initiate Purchase - Monthly Subscription

**Goal:** Complete one purchase transaction

**iOS Steps:**
```
1. Tap "Monthly" subscription button
2. iOS presents: Purchase Confirmation Sheet
   "Confirm your subscription?"
   - Monthly Premium
   - $12.99/month (or localized)
   - "First 7 Days Free" (if trial enabled)
3. Verify: Merchant name is Apple
4. Tap "Subscribe" button
5. Face/Touch ID prompt appears
6. Complete authentication
7. Wait 3-5 seconds for processing
8. Expect: Success screen
   ✅ "Thank you! Your subscription is active"
   ✅ Show expiry date
9. Tap "Continue to App"
10. Verify: Premium features unlock
```

**Android Steps:**
```
1. Tap "Subscribe Monthly" button
2. Google Play payment sheet appears:
   - Google Play Billing Library prompt
   - Confirm: $12.99/month
   - Billing account dropdown (if multiple)
3. Verify: Merchant is "Google LLC"
4. Tap "Buy"
5. If new payment method:
   - Biometric/PIN authentication
   - First-time payment consent
6. Wait 5-10 seconds
7. Payment reserved (sandbox, no actual charge)
8. Play Billing library closes
9. App shows: ✅ "Subscription activated"
10. Check: Features now available
```

**Expected Result:** ✅
```
- Payment completes successfully
- No error messages
- User subscription status: "premium"
- Features unlock immediately
- Expiry date shows correctly
```

**Failure Scenarios:**
```
❌ "Unable to make purchase" error
   → Check: Billing method valid
   → Check: Test account in sandbox mode
   → Check: Parental controls not blocking

❌ Payment successful but features don't unlock
   → Check: VerifySubscriptionView endpoint works
   → Check: Backend received webhook
   → Check: MongoDB user_subscriptions updated

❌ "Subscription failed. Try again" after 5 retries
   → Check: RevenueCat service available
   → Check: Network connectivity stable
   → Check: No rate limiting on backend
```

### Test Case 5: Verify Subscription Status (Backend Sync)

**Goal:** Confirm backend receives and processes purchase

**Backend Verification Steps:**
```bash
# Query MongoDB directly
mongosh
> use facesyma-backend
> db.user_subscriptions.findOne({user_id: 123})

Expected output:
{
  "_id": ObjectId(...),
  "user_id": 123,
  "plan": "premium",          ← Should be "premium" not "free"
  "provider": "revenuecat",
  "entitlements": {
    "premium": true           ← Entitlement granted
  },
  "subscriptions": {
    "monthly_tier_d": {       ← Based on region
      "expires_date": "2025-04-19T...",
      "is_sandbox": true      ← Sandbox purchase
    }
  },
  "original_purchase_date": "2026-04-19T...",
  "expires_date": "2026-05-19T...",
  "verified_at": "2026-04-19T14:32:00Z"
}

# Check appfaceapi_myuser collection
> db.appfaceapi_myuser.findOne({id: 123})
{
  ...
  "plan": "premium",          ← Updated from "free"
  "updated_at": "2026-04-19T14:32:00Z"
}
```

**API Endpoint Verification:**
```bash
# Check subscription status via API
curl 'http://localhost:8000/api/subscription/status/123/'

Expected response:
{
  "plan": "premium",
  "active": true,
  "entitlements": ["premium"],
  "expires_date": "2026-05-19T...",
  "verified_at": "2026-04-19T14:32:00Z"
}

# Check feature access
curl 'http://localhost:8000/api/subscription/feature/123/?feature=unlimited_checks'

Expected response:
{
  "feature": "unlimited_checks",
  "has_access": true,
  "plan": "premium",
  "upgrade_required": false
}
```

**Expected Result:** ✅
```
- MongoDB updated within 10 seconds
- User plan changed from "free" to "premium"
- Entitlements granted
- API endpoints return premium status
```

**Failure Scenarios:**
```
❌ MongoDB not updated after 30 seconds
   → Check: VerifySubscriptionView endpoint logs
   → Check: RevenueCat API responds correctly
   → Check: Network between app and backend

❌ Backend shows "free" despite purchase
   → Check: Webhook secret configured correctly
   → Check: Subscription verification call made
   → Check: RevenueCat API key valid

❌ API endpoint returns 500 error
   → Check: Backend server running
   → Check: MongoDB connection working
   → Check: user_subscriptions collection exists
```

### Test Case 6: Feature Access Control - Premium Features

**Goal:** Verify premium features only available to premium users

**iOS/Android Steps:**
```
1. After successful purchase, navigate to meal game
2. Expect: Game loads immediately
   ✓ Access granted
   ✓ No paywall shown
3. Return to profile, sign out
4. Sign in with DIFFERENT account (free user)
5. Navigate to meal game
6. Expect: Paywall displayed
   ✓ "Upgrade to Premium"
   ✓ Price shown
   ✓ "Upgrade" button tappable

Test Premium Features:
  ✓ Meal game access → Check via API
  ✓ Social challenges → Check via API
  ✓ Advanced search → Functionality enabled
  ✓ Unlimited checks → Count doesn't decrease
  ✓ Priority support → Badge shows
```

**Backend Verification:**
```bash
# Premium user (user_id=123)
curl 'http://localhost:8000/api/subscription/feature/123/?feature=meal_game_access'
→ {"has_access": true, ...}

curl 'http://localhost:8000/api/subscription/feature/123/?feature=social_challenges'
→ {"has_access": true, ...}

# Free user (user_id=456)
curl 'http://localhost:8000/api/subscription/feature/456/?feature=meal_game_access'
→ {"has_access": false, ...}
```

**Expected Result:** ✅
```
- Premium user: All features unlocked
- Free user: Paywall shows for premium features
- Feature matrix enforced correctly
- API access controlled by backend
```

### Test Case 7: Subscription Cancellation

**Goal:** User can cancel subscription

**iOS Steps:**
```
1. Settings → [Your Name] → Subscriptions
2. Find: "Facesyma Premium"
3. Tap: "Manage Subscription"
4. Tap: "Cancel Subscription"
5. Confirm: "Confirm Cancellation"
6. App receives: Cancellation notification
7. Expect message: "Your subscription will end on [date]"
8. Wait 5 seconds, then refresh app
9. Check: plan still "premium" until expiry
10. After expiry: plan reverts to "free"
```

**Android Steps:**
```
1. Google Play Store → Profile → Payments and subscriptions
2. Find: "Facesyma Premium"
3. Tap: "Manage"
4. Tap: "Cancel Subscription"
5. Select reason (optional)
6. Confirm: "Cancel Subscription"
7. Receive: Confirmation email
8. App receives: Cancellation webhook
9. Check: Subscription shows "Cancelled"
   - Still active until renewal date
   - No charge on next renewal
```

**Backend Verification:**
```bash
# After cancellation
mongosh
> db.user_subscriptions.findOne({user_id: 123})

{
  ...
  "plan": "premium",           ← Still premium until expiry
  "cancelled_at": "2026-04-19T15:00:00Z",
  "is_active": true            ← True until expiry date passes
}

# On expiry date + 1 day
curl 'http://localhost:8000/api/subscription/status/123/'

Response should show:
{
  "plan": "free",              ← Downgraded after expiry
  "active": false
}
```

**Expected Result:** ✅
```
- Cancellation succeeds
- No charge on renewal
- User still has access until expiry
- Features revoke after expiry date
```

### Test Case 8: Restore Previous Purchases

**Goal:** User can restore subscription on new device

**Scenario:** User upgraded, then logged in on new device

**iOS Steps:**
```
1. Fresh install of TestFlight app
2. Login with same account (test-ios-1@example.com)
3. Tap: "Restore Purchases" (in settings)
4. Wait 5 seconds
5. RevenueCat syncs past purchases
6. Expect: plan shows "premium"
   ✓ Subscription reactivated
   ✓ Expiry date correct
7. Features immediately available
8. No repayment needed
```

**Android Steps:**
```
1. Uninstall app
2. Reinstall from Play Store
3. Login with same account
4. Tap: "Restore Subscription"
5. Google Play Billing queries:
   "Do you have an active subscription?"
6. Returns: Active premium subscription
7. App syncs to backend
8. Expect: plan shows "premium"
9. Features unlocked without repayment
```

**Backend Verification:**
```bash
# After restore, user should have:
mongosh
> db.user_subscriptions.findOne({user_id: 123})

{
  "plan": "premium",           ← Restored
  "provider": "revenuecat",
  "verified_at": "2026-04-20T10:00:00Z"  ← New timestamp
}
```

**Expected Result:** ✅
```
- Subscription restored instantly
- No new payment charged
- Expiry date preserved
- Access fully functional
```

### Test Case 9: Free Trial Flow (If Enabled)

**Goal:** Verify free trial works correctly

**iOS Steps (Sandbox Only):**
```
1. New sandbox test account
   test-ios-2@example.com
2. Login to app
3. Navigate to Premium
4. Tap "Monthly" subscription
5. Confirm: "First 7 Days Free"
   - Then $12.99/month
6. Complete purchase
7. No charge appears
8. User gets premium access
9. Verify: expires_date = now + 7 days
10. After 7 days: Subscription renews (charges)
```

**Backend Verification:**
```bash
# Trial user
mongosh
> db.user_subscriptions.findOne({user_id: 789})

{
  "plan": "premium",
  "trial_started": "2026-04-20T...",
  "trial_ends": "2026-04-27T...",  ← 7 days from start
  "original_purchase_date": "2026-04-20T...",
  "is_trial": true
}
```

**Expected Result:** ✅
```
- Trial purchase completes
- No payment charged
- User gets premium access
- Renewal email sent before trial ends
- Automatic renewal after 7 days
```

### Test Case 10: Regional Pricing Display

**Goal:** Verify correct pricing for different regions

**Test Different Regions:**

```
Tier A (India - INR):
  Expected: ₹79/month or ₹679/year
  Device: India phone with IN region
  Play Store: Switched to India account

Tier C (Japan - JPY):
  Expected: ¥590/month or ¥4,990/year
  Device: Japan phone with JA region
  App Store: Switched to Japan account

Tier D (USA - USD):
  Expected: $12.99/month or $99.99/year
  Device: US phone with US region
  Play Store: US account

Tier E (Germany - EUR):
  Expected: €7.99/month or €79.99/year
  Device: German phone with DE region
  Play Store: German account
```

**Verification:**
```
For each region:
1. Install app
2. Login
3. Go to Premium screen
4. Verify: Price in correct currency
5. Verify: Amount matches tier
6. Confirm: Currency symbol correct
```

**Expected Result:** ✅
```
- All 5 tiers display correct pricing
- Currency symbols localized
- Prices auto-converted by RevenueCat
- No manual override needed
```

## Test Execution Matrix

| Test Case | iOS | Android | Desktop | Expected | Status |
|-----------|-----|---------|---------|----------|--------|
| 1. SDK Init | ✅ | ✅ | N/A | No errors | |
| 2. Login | ✅ | ✅ | N/A | User ID sync | |
| 3. Get Packages | ✅ | ✅ | N/A | Pricing correct | |
| 4. Monthly Purchase | ✅ | ✅ | N/A | Payment success | |
| 5. Backend Sync | ✅ | ✅ | ✅ | DB updated | |
| 6. Feature Access | ✅ | ✅ | N/A | Features unlock | |
| 7. Cancellation | ✅ | ✅ | N/A | Access until expiry | |
| 8. Restore | ✅ | ✅ | N/A | Reactivated | |
| 9. Free Trial | ✅ | ✅ | N/A | 7 days free | |
| 10. Regional Pricing | ✅ | ✅ | N/A | Correct tier | |

## Critical Path Flow

### Minimal Happy Path (must test before launch)

```
1. ✅ App initializes
2. ✅ User logs in
3. ✅ Sees subscription packages
4. ✅ Purchases monthly subscription
5. ✅ Backend records purchase
6. ✅ Features unlock
7. ✅ User can see their premium status
```

### Extended Testing (before public release)

```
1. ✅ Critical path
2. ✅ Trial flow (if enabled)
3. ✅ Cancellation flow
4. ✅ Restore purchases
5. ✅ 3+ different regions
6. ✅ Both iOS and Android
7. ✅ Backend API verification
```

## Regression Tests (Before Each Release)

```
Every app update, verify:

□ Purchase still works (no breaking changes)
□ Feature access not broken
□ Subscription status correct
□ Cancellation still functional
□ Restore purchases works
□ Regional pricing displays
□ No new error messages
□ No network timeout issues
```

## Test Report Template

```markdown
# Subscription E2E Test Report - [Date]

## Environment
- Device: [Model, OS Version]
- App Version: [1.x.x]
- RevenueCat: [Version]
- Region: [Country]
- Backend: [Staging/Production]

## Test Results

| Test Case | Result | Notes |
|-----------|--------|-------|
| 1. SDK Init | ✅ PASS | No errors |
| 2. Login | ✅ PASS | User ID 123 |
| ... | | |

## Issues Found
1. [Description] - Severity: [High/Medium/Low]
   - Steps to reproduce
   - Expected vs actual
   - Workaround

## Sign-off
- Tester: [Name]
- Date: [YYYY-MM-DD]
- Status: APPROVED / BLOCKED
```

## Next Steps

1. Set up TestFlight beta for iOS testers
2. Set up Google Play Beta track for Android testers
3. Execute critical path tests
4. Document findings in test report
5. Fix any critical issues before public launch
6. Execute extended tests on both platforms
7. Get sign-off from QA
8. Launch to public 🚀
