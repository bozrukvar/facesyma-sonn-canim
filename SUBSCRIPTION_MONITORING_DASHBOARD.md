# Production Monitoring & Analytics Dashboard

## Overview

Real-time subscription metrics, revenue tracking, and alerting for Facesyma premium tier.

## Part 1: RevenueCat Dashboard

### Key Metrics (Automatic)

RevenueCat Dashboard: https://dashboard.revenuecat.com

#### Revenue Metrics

**Monthly Recurring Revenue (MRR)**
```
Definition: Total predictable monthly subscription revenue
Formula: Sum of all active monthly subscriptions + (annual subscriptions / 12)

Location: Dashboard → Analytics → MRR
Target: $10,000+ MRR by Month 12
Healthy Growth: +20% month-over-month
```

**Annual Recurring Revenue (ARR)**
```
Definition: MRR × 12
Current Example: $5,000 MRR = $60,000 ARR
```

**Customer Lifetime Value (LTV)**
```
Definition: Average revenue per subscriber over their lifetime
Formula: Average subscription value × Average subscription duration
Target: $120+ (assuming 10 months average)
Healthy: LTV > CAC (Customer Acquisition Cost)
```

#### Subscription Metrics

**Active Subscriptions**
```
Location: Dashboard → Overview
Shows:
  ├── Total active subscriptions
  ├── By tier (A, B, C, D, E)
  ├── By platform (iOS, Android)
  └── Trend (daily/weekly/monthly)

Healthy Target:
  Week 1: 10-50 active
  Month 1: 200+ active
  Month 3: 500+ active
  Month 6: 1,000+ active
```

**New Subscribers**
```
Location: Analytics → Subscriptions
Shows:
  ├── Daily new subscriptions
  ├── First trial conversions
  ├── Paid first month conversions
  └── Cumulative total

Track:
  - New subscribers/day
  - Week-over-week growth
  - Source (organic, ads, etc.)
```

**Conversion Metrics**
```
Conversion Rate = (Paid subscriptions / Trial starts) × 100

Location: Analytics → Funnel
Target: 15-25% conversion (trial to paid)
Healthy: 20%+ conversion

If <10%:
  → Issue with trial → paid experience
  → Consider: Onboarding, pricing, messaging
```

**Churn Rate**
```
Definition: % of subscribers who cancel per month
Formula: Cancelled subscriptions / Beginning subscribers

Location: Analytics → Retention
Target: <5% monthly churn
Healthy Range: 3-5%
Warning: >8% churn indicates product issues

High Churn Signals:
  ├── Product not delivering value
  ├── Pricing too high for region
  ├── Bugs/crashes in premium features
  ├── Poor customer support
  └── Competitor offering better value
```

**Retention by Cohort**
```
Location: Analytics → Cohorts
Shows retention % by signup date

Day 1: 100% (just subscribed)
Day 7: ~75% (lost 25% immediately)
Day 30: ~50% (lost half by month end)
Day 90: ~30% (90-day retention)

Healthy Retention:
  - Day 7: >70%
  - Day 30: >50%
  - Day 90: >30%

If retention is poor:
  → Improve onboarding
  → Fix bugs in premium features
  → Increase engagement
```

### RevenueCat Custom Alerts

**Setup in RevenueCat Dashboard:**

```
Alerts → Create Alert

Alert 1: Sudden Revenue Drop
  Metric: MRR
  Condition: Drops >20% from 7-day average
  Notification: Slack + Email
  Frequency: Daily at 10am

Alert 2: High Churn Spike
  Metric: Churn Rate
  Condition: Exceeds 8% in 24-hour period
  Notification: Slack + Email
  Frequency: Real-time

Alert 3: Conversion Drop
  Metric: Trial to Paid Conversion
  Condition: Below 15%
  Notification: Email
  Frequency: Daily

Alert 4: Critical Subscription Failures
  Metric: Failed Purchases
  Condition: >5% of total purchase attempts
  Notification: Slack (urgent)
  Frequency: Real-time
```

## Part 2: Backend Monitoring

### MongoDB Subscription Queries

#### Real-Time Subscriber Count

```javascript
// Current subscribers
db.user_subscriptions.countDocuments({
  plan: "premium",
  expires_date: { $gt: new Date() }
})

// By tier (assuming tier stored in metadata)
db.user_subscriptions.aggregate([
  { $match: { plan: "premium", expires_date: { $gt: new Date() } } },
  { $group: { _id: "$tier", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])

// Result:
// { _id: "tier_d", count: 450 }
// { _id: "tier_c", count: 320 }
// { _id: "tier_e", count: 200 }
// { _id: "tier_b", count: 150 }
// { _id: "tier_a", count: 280 }
```

#### Revenue Calculation

```javascript
// Total revenue from active subscriptions
db.user_subscriptions.aggregate([
  { $match: { plan: "premium", expires_date: { $gt: new Date() } } },
  { $group: { 
      _id: "$tier",
      count: { $sum: 1 },
      total_revenue: { $sum: "$monthly_price" }  // If storing price
    } 
  }
])

// Or query payment transactions
db.payment_transactions.aggregate([
  { $match: { 
      provider: "revenuecat",
      status: "completed",
      created_at: { $gte: ISODate("2026-04-01T00:00:00Z") }
    } 
  },
  { $group: { 
      _id: null,
      total_revenue: { $sum: "$amount" },
      transaction_count: { $sum: 1 }
    } 
  }
])
```

#### Churn Tracking

```javascript
// Cancelled subscriptions (last 30 days)
db.user_subscriptions.countDocuments({
  plan: "free",
  cancelled_at: { 
    $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  }
})

// By tier
db.user_subscriptions.aggregate([
  { $match: {
      cancelled_at: { 
        $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      }
    }
  },
  { $group: { 
      _id: "$tier",
      cancelled_count: { $sum: 1 }
    } 
  }
])
```

#### Payment Failures

```javascript
// Failed or pending payments
db.payment_transactions.countDocuments({
  status: { $in: ["failed", "pending"] }
})

// Failures by provider
db.payment_transactions.aggregate([
  { $match: { status: "failed" } },
  { $group: { 
      _id: "$provider",
      failed_count: { $sum: 1 },
      total_amount_failed: { $sum: "$amount" }
    }
  }
])
```

### Backend API Monitoring Endpoints

Create monitoring endpoints:

```python
# admin_api/views/subscription_monitoring_views.py

class SubscriptionMetricsView(View):
    """Real-time subscription metrics"""
    
    def get(self, request):
        db = _get_db()
        subscriptions = db['user_subscriptions']
        
        now = datetime.now().isoformat()
        active_subs = subscriptions.count_documents({
            'plan': 'premium',
            'expires_date': {'$gt': now}
        })
        
        cancelled_30d = subscriptions.count_documents({
            'cancelled_at': {'$exists': True},
            'cancelled_at': {
                '$gte': (datetime.now() - timedelta(days=30)).isoformat()
            }
        })
        
        by_tier = list(subscriptions.aggregate([
            {'$match': {'plan': 'premium'}},
            {'$group': {
                '_id': '$provider',
                'count': {'$sum': 1}
            }}
        ]))
        
        return JsonResponse({
            'active_subscriptions': active_subs,
            'cancelled_30d': cancelled_30d,
            'churn_rate_30d': (cancelled_30d / active_subs * 100) if active_subs > 0 else 0,
            'by_tier': by_tier,
            'timestamp': datetime.now().isoformat()
        })
```

Add to URLs:
```python
path('monitoring/subscriptions/', SubscriptionMetricsView.as_view(), name='subscription-metrics')
```

## Part 3: Dashboard Setup

### Option A: RevenueCat Dashboard (Recommended)

**No setup needed** — RevenueCat provides everything automatically.

**Link:** https://dashboard.revenuecat.com/projects/[PROJECT-ID]

**Daily Routine:**
```
Morning (10am):
  ✓ Check: MRR vs yesterday
  ✓ Check: New subscriptions
  ✓ Check: Churn alert triggered?
  ✓ Check: Failed transactions

Weekly (Monday 9am):
  ✓ Review: Cohort retention
  ✓ Review: Conversion funnel
  ✓ Review: Revenue trend
  ✓ Compare: Tier A-E performance

Monthly (1st of month):
  ✓ Analyze: Month-over-month growth
  ✓ Analyze: Regional performance
  ✓ Analyze: LTV vs CAC
  ✓ Plan: Next month improvements
```

### Option B: Custom Grafana Dashboard

**Create custom dashboard for internal metrics:**

```bash
# 1. Install Grafana
docker run -d --name=grafana \
  -p 3000:3000 \
  grafana/grafana:latest

# 2. Add MongoDB data source
# Configuration → Data Sources → Add MongoDB

# 3. Create Dashboards
# Create charts:
#   - Active subscriptions (time series)
#   - Revenue MRR (gauge)
#   - Churn rate (gauge)
#   - Conversion rate (gauge)
#   - Failed transactions (table)
#   - By tier breakdown (pie chart)
```

**Sample Grafana Query:**

```
# Active subscriptions (MongoDB)
db.user_subscriptions.countDocuments({
  plan: "premium",
  expires_date: { $gt: new Date() }
})
```

### Option C: Google Sheets (Simple)

**Track metrics manually in spreadsheet:**

```
Date | Active | MRR | Conversions | Churn | Notes
-----|--------|-----|-------------|-------|-------
4/20 | 450    | 6,200 | 25% | 4.2% | Normal week
4/21 | 455    | 6,300 | 26% | 3.8% | Weekend dip
...
```

## Part 4: Observability & Logging

### Log Subscription Events

Modify subscription_views.py to log events:

```python
import logging
log = logging.getLogger(__name__)

class VerifySubscriptionView(View):
    def post(self, request):
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        # Log verification attempt
        log.info(f"Subscription verification: user_id={user_id}")
        
        # ... process ...
        
        # Log success
        log.info(f"✅ Subscription verified: user_id={user_id}, plan=premium")
        
        # Log to MongoDB for analytics
        db['subscription_events'].insert_one({
            'event': 'subscription_verified',
            'user_id': user_id,
            'plan': 'premium',
            'timestamp': datetime.now().isoformat()
        })
```

### Key Events to Log

```
1. purchase_initiated
   - user_id, package_id, tier

2. purchase_completed
   - user_id, amount, currency, transaction_id

3. purchase_failed
   - user_id, error_code, reason

4. subscription_verified
   - user_id, plan, expires_date

5. subscription_cancelled
   - user_id, reason, timestamp

6. subscription_expired
   - user_id, auto_downgraded_to_free

7. refund_issued
   - user_id, amount, reason

8. trial_started
   - user_id, ends_date

9. trial_conversion
   - user_id, converted_to_paid
```

## Part 5: Alerting Strategy

### Critical Alerts (Immediate Action)

```
1. Revenue Crashed (>30% drop in 1 hour)
   Notification: Slack (urgent) + PagerDuty
   Action: Investigate RevenueCat/backend
   
2. >50% Purchase Failure Rate
   Notification: Slack (urgent) + PagerDuty
   Action: Check billing provider status
   
3. Backend Sync Failures (>10% of transactions)
   Notification: Slack (urgent)
   Action: Check VerifySubscriptionView logs
```

### Warning Alerts (Review within 4 hours)

```
1. Churn Rate >8%
   Notification: Slack (warning)
   Action: Investigate why users cancel
   
2. Conversion Rate <15%
   Notification: Email
   Action: Improve trial → paid experience
   
3. High Refund Rate (>2%)
   Notification: Email
   Action: Review refund reasons
```

### Informational (Daily Report)

```
1. Daily metrics email at 10am
   - Total active subscriptions
   - New subscriptions
   - Revenue (USD)
   - Churn rate

2. Weekly cohort report (Monday)
   - Retention curves
   - LTV trend
   - Tier performance
```

## Part 6: Performance Targets

### Month 1 (MVP Launch)

```
Active Subscriptions: 10-50
MRR: $200-500
Conversion Rate: 15%+
Churn Rate: <10%
```

### Month 3

```
Active Subscriptions: 200-500
MRR: $2,000-3,000
Conversion Rate: 18%+
Churn Rate: <8%
```

### Month 6

```
Active Subscriptions: 800-1,500
MRR: $8,000-12,000
Conversion Rate: 20%+
Churn Rate: <5%
LTV:$150+
```

### Month 12

```
Active Subscriptions: 2,000+
MRR: $20,000+
Conversion Rate: 22%+
Churn Rate: <5%
LTV: $200+
```

## Part 7: Monthly Review Checklist

```markdown
# Subscription Performance Review - [Month]

## Revenue
- [ ] MRR: $[amount] (↑/↓ [%] vs last month)
- [ ] ARR: $[amount]
- [ ] Total transactions: [count]
- [ ] Failed transactions: [count] ([%])

## Subscriber Metrics
- [ ] Active: [count] (↑/↓ [%])
- [ ] New: [count]
- [ ] Cancelled: [count]
- [ ] Churn rate: [%]

## Conversion
- [ ] Trial starts: [count]
- [ ] Trial conversions: [count]
- [ ] Conversion rate: [%]
- [ ] Refunds: [count] ([%])

## Regional Performance
- [ ] Tier A: [count] subs, $[revenue]
- [ ] Tier B: [count] subs, $[revenue]
- [ ] Tier C: [count] subs, $[revenue]
- [ ] Tier D: [count] subs, $[revenue]
- [ ] Tier E: [count] subs, $[revenue]

## Platform Performance
- [ ] iOS: [count] subs
- [ ] Android: [count] subs
- [ ] iOS conversion: [%]
- [ ] Android conversion: [%]

## Issues Found
- [ ] [Issue 1] - Impact: High
- [ ] [Issue 2] - Impact: Medium

## Actions for Next Month
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3

## Approval
- Reviewed by: [Name]
- Date: [YYYY-MM-DD]
```

## Part 8: Dashboards at a Glance

### Main Dashboard (for stakeholders)

```
┌─────────────────────────────────────────────────┐
│          Facesyma Subscription Status            │
├─────────────────────────────────────────────────┤
│ Active Subscriptions: 1,245 ↑↑↑ (+12% MoM)      │
│ MRR: $18,500 ↑↑ (+15% MoM)                      │
│ Conversion Rate: 21% ↑ (+2% MoM)                │
│ Churn Rate: 4.2% ↓ (-0.8% MoM)                  │
├─────────────────────────────────────────────────┤
│ Top Tier: Tier D (450 subs, $5,850 MRR)         │
│ Growth Leader: Tier A (280 subs, +25% MoM)      │
│ Highest Value: Tier E (200 subs, $1,600/mo)    │
├─────────────────────────────────────────────────┤
│ Platform Split: iOS 60%, Android 40%            │
│ Platform Conversions: iOS 22%, Android 19%      │
├─────────────────────────────────────────────────┤
│ ⚠️  Alert: Churn above 4% (monitor)             │
│ ✅ All systems healthy                          │
└─────────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Access RevenueCat Dashboard
2. ✅ Set up critical alerts
3. ✅ Create backend monitoring endpoint
4. → Deploy monitoring to production
5. → Set up daily email reports
6. → Train team on interpreting metrics
7. → Schedule weekly metric reviews
