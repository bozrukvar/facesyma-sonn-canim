# Hybrid Leaderboard API — Phase 6 Gamification

**Date**: 2026-04-19  
**Status**: ✅ Complete  
**Tokens**: 768

---

## Overview

Hybrid leaderboards provide global, trait-based, and community-specific rankings. Users are ranked by coins, badges, meals, or accuracy with optional time period filtering. Supports pagination, user rank lookup, and extensible sorting metrics.

---

## Data Models

### LeaderboardEntry

```python
{
    "rank": 1,
    "user_id": 123,
    "username": "user_123",
    "avatar": "https://...",
    "coins_balance": 500,
    "total_coins_earned": 2500,
    "platinum_badges": 2,           # Platinum tier badge count
    "gold_and_above": 5,            # Gold + Platinum count
    "meals_completed": 45,          # Optional
    "challenges_won": 12,           # Optional
    "avg_accuracy": 87.5,           # Optional
    "top_traits": ["dürüst", "analitik", "yaratıcı"]
}
```

### LeaderboardResponse

```python
{
    "leaderboard_type": "global",  # "global" | "trait" | "community"
    "leaderboard_name": "Global Leaderboard",
    "time_period": "all_time",     # "all_time" | "this_month" | "this_week"
    "sort_by": "coins",            # "coins" | "badges" | "meals" | "accuracy"
    "total_entries": 523,          # Users matching filter
    "user_rank": 45,               # Current user's rank (null if not in results)
    "cached": false,
    "cache_expiry": null,
    "entries": [LeaderboardEntry, ...]
}
```

### LeaderboardFilter

```python
{
    "leaderboard_type": "global",
    "trait_id": null,              # Required for trait leaderboards
    "community_id": null,          # Required for community leaderboards
    "time_period": "all_time",
    "sort_by": "coins",
    "limit": 100,                  # 1–1000
    "offset": 0
}
```

---

## API Endpoints

### 1. Hybrid Leaderboard (Dispatcher)

Unified endpoint supporting all leaderboard types via filter parameters.

**Endpoint**
```
GET /api/v1/leaderboards/
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `leaderboard_type` | string | `global` | `global`, `trait`, `community` |
| `trait_id` | string | null | Required if `leaderboard_type=trait` |
| `community_id` | int | null | Required if `leaderboard_type=community` |
| `time_period` | string | `all_time` | `all_time`, `this_month`, `this_week` |
| `sort_by` | string | `coins` | `coins`, `badges`, `meals`, `accuracy` |
| `limit` | int | 100 | 1–1000 |
| `offset` | int | 0 | Pagination |

**Request**
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/?leaderboard_type=global&sort_by=coins&limit=50&offset=0" \
  -H "Authorization: Bearer <user_token>"
```

**Response (200 OK)**
```json
{
  "leaderboard_type": "global",
  "leaderboard_name": "Global Leaderboard",
  "time_period": "all_time",
  "sort_by": "coins",
  "total_entries": 523,
  "user_rank": 45,
  "cached": false,
  "cache_expiry": null,
  "entries": [
    {
      "rank": 1,
      "user_id": 101,
      "username": "ali_expert",
      "avatar": "https://...",
      "coins_balance": 5000,
      "total_coins_earned": 12000,
      "platinum_badges": 4,
      "gold_and_above": 8,
      "meals_completed": 120,
      "challenges_won": 25,
      "avg_accuracy": 92.3,
      "top_traits": ["dürüst", "lider", "analitik"]
    },
    {
      "rank": 2,
      "user_id": 102,
      "username": "fatih_gamer",
      "avatar": null,
      "coins_balance": 4800,
      "total_coins_earned": 11500,
      "platinum_badges": 3,
      "gold_and_above": 7,
      "meals_completed": 110,
      "challenges_won": 22,
      "avg_accuracy": 90.1,
      "top_traits": ["rekabet_severi", "stratejik", "yaratıcı"]
    }
  ]
}
```

**Error Response (400)**
```json
{
  "detail": "Invalid parameter: trait_id"
}
```

**Error Response (401)**
```json
{
  "detail": "Unauthorized"
}
```

---

### 2. Global Leaderboard

Ranks all users globally by selected metric.

**Endpoint**
```
GET /api/v1/leaderboards/global/
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `time_period` | string | `all_time` | `all_time`, `this_month`, `this_week` |
| `sort_by` | string | `coins` | `coins`, `badges`, `meals`, `accuracy` |
| `limit` | int | 100 | 1–1000 |
| `offset` | int | 0 | Pagination |

**Request**
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/global/?sort_by=badges&limit=20&offset=0" \
  -H "Authorization: Bearer <user_token>"
```

**Response (200 OK)**
```json
{
  "leaderboard_type": "global",
  "leaderboard_name": "Global Leaderboard",
  "time_period": "all_time",
  "sort_by": "badges",
  "total_entries": 523,
  "user_rank": 18,
  "entries": [
    {
      "rank": 1,
      "user_id": 201,
      "username": "badge_collector",
      "avatar": "https://...",
      "coins_balance": 3500,
      "total_coins_earned": 8000,
      "platinum_badges": 6,
      "gold_and_above": 12,
      "meals_completed": 85,
      "challenges_won": 30,
      "avg_accuracy": 88.5,
      "top_traits": ["dürüst", "doğallık", "empati"]
    }
  ]
}
```

---

### 3. Trait-Based Leaderboard

Ranks users who have a specific sıfat in their top 3 traits.

**Endpoint**
```
GET /api/v1/leaderboards/trait/
```

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `trait_id` | string | ✅ Yes | Sıfat ID (e.g., `dürüst`, `analitik`) |
| `time_period` | string | | `all_time`, `this_month`, `this_week` |
| `sort_by` | string | | `coins`, `badges`, `meals`, `accuracy` |
| `limit` | int | | 1–1000 (default 100) |
| `offset` | int | | Pagination (default 0) |

**Request**
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/trait/?trait_id=dürüst&sort_by=coins&limit=50" \
  -H "Authorization: Bearer <user_token>"
```

**Response (200 OK)**
```json
{
  "leaderboard_type": "trait",
  "leaderboard_name": "Trait-Based: dürüst",
  "trait_id": "dürüst",
  "time_period": "all_time",
  "sort_by": "coins",
  "total_entries": 156,
  "user_rank": 12,
  "entries": [
    {
      "rank": 1,
      "user_id": 301,
      "username": "honesty_first",
      "avatar": "https://...",
      "coins_balance": 4200,
      "total_coins_earned": 10000,
      "platinum_badges": 2,
      "gold_and_above": 5,
      "meals_completed": 95,
      "challenges_won": 15,
      "avg_accuracy": 91.2,
      "top_traits": ["dürüst", "doğallık", "empati"]
    }
  ]
}
```

**Error Response (400)**
```json
{
  "detail": "Missing trait_id"
}
```

---

### 4. Community Leaderboard

Ranks users within a specific community.

**Endpoint**
```
GET /api/v1/leaderboards/community/
```

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `community_id` | int | ✅ Yes | Community ID |
| `time_period` | string | | `all_time`, `this_month`, `this_week` |
| `sort_by` | string | | `coins`, `badges`, `meals`, `accuracy` |
| `limit` | int | | 1–1000 (default 100) |
| `offset` | int | | Pagination (default 0) |

**Request**
```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/community/?community_id=42&sort_by=meals&limit=30" \
  -H "Authorization: Bearer <user_token>"
```

**Response (200 OK)**
```json
{
  "leaderboard_type": "community",
  "leaderboard_name": "Community #42",
  "community_id": 42,
  "time_period": "all_time",
  "sort_by": "meals",
  "total_entries": 87,
  "user_rank": 5,
  "entries": [
    {
      "rank": 1,
      "user_id": 401,
      "username": "meal_master",
      "avatar": "https://...",
      "coins_balance": 2500,
      "total_coins_earned": 6000,
      "platinum_badges": 1,
      "gold_and_above": 3,
      "meals_completed": 150,
      "challenges_won": 8,
      "avg_accuracy": 85.7,
      "top_traits": ["meraklı", "yaratıcı", "sosyal"]
    }
  ]
}
```

**Error Response (400)**
```json
{
  "detail": "Missing community_id"
}
```

---

## Sorting Metrics

| Sort By | Field | Description |
|---------|-------|-------------|
| `coins` | `total_coins_earned` | Lifetime coins earned |
| `badges` | `badges.platinum_count` | Count of platinum-tier badges |
| `meals` | `meals_completed` | Total meals completed |
| `accuracy` | `avg_accuracy` | Average accuracy across meals/challenges |

---

## Time Period Filtering

Filters users by `date_joined` (simplified — would benefit from timestamped metrics):

| Period | Filter |
|--------|--------|
| `all_time` | No filter |
| `this_month` | `date_joined` ≥ 30 days ago |
| `this_week` | `date_joined` ≥ 7 days ago |

---

## User Rank Lookup

If the authenticated user is in the leaderboard results, `user_rank` is populated:

```json
{
  "leaderboard_type": "global",
  "total_entries": 523,
  "user_rank": 45,
  "entries": [...]
}
```

If not in results (e.g., offset too high):
```json
{
  "user_rank": null
}
```

---

## Caching Strategy (MVP)

Current implementation: **No caching** (`cached: false`).

**Phase 2 Enhancement**: Implement Redis caching with TTL:

```python
# Model definition ready (LeaderboardCacheConfig)
global_ttl: 300      # 5 minutes
trait_ttl: 300
community_ttl: 300

# Cache key pattern
lb:global:{time_period}:{sort_by}:{offset}:{limit}
lb:trait:{trait_id}:{time_period}:{sort_by}:{offset}:{limit}
lb:community:{community_id}:{time_period}:{sort_by}:{offset}:{limit}
```

---

## Integration Points

### Badge Service
```python
from gamification.services.badge_service import BadgeService

# Leaderboards reference badge tiers
platinum_count = len([b for b in user.badges.values() if b.get("current_tier") == "platinum"])
```

### Coin Service
```python
from core.services.coin_service import CoinService

# total_coins_earned sourced from user.total_coins_earned (maintained by CoinService)
```

### User Model
```python
# Required fields:
appfaceapi_myuser.coins
appfaceapi_myuser.total_coins_earned
appfaceapi_myuser.badges       # Dict of badge_id → {current_tier, progress}
appfaceapi_myuser.meals_completed
appfaceapi_myuser.challenges_won
appfaceapi_myuser.avg_accuracy
appfaceapi_myuser.top_sifats   # List of 3 personality traits
appfaceapi_myuser.community_id # For community leaderboard filtering
appfaceapi_myuser.date_joined  # For time_period filtering
```

---

## Error Handling

| Status | Error | Cause |
|--------|-------|-------|
| 400 | `Invalid parameter` | Query param out of range or wrong type |
| 400 | `Missing trait_id` | Trait leaderboard requested without `trait_id` |
| 400 | `Invalid community_id` | `community_id` not integer |
| 400 | `Leaderboard error` | Service-level error |
| 401 | `Unauthorized` | Missing/invalid auth token |
| 500 | `Internal server error` | Unexpected exception |

---

## Example Workflows

### Get Top 50 Users Globally (Coins)

```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/global/?limit=50&offset=0" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Get User's Rank Among "dürüst" Sıfat Community

```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/trait/?trait_id=dürüst&limit=1&offset=0" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

Response includes `user_rank` if user has "dürüst" trait.

### Paginate Through Community Leaderboard

```bash
# Page 1
curl -X GET "http://localhost:8000/api/v1/leaderboards/community/?community_id=42&limit=10&offset=0"

# Page 2
curl -X GET "http://localhost:8000/api/v1/leaderboards/community/?community_id=42&limit=10&offset=10"

# Page 3
curl -X GET "http://localhost:8000/api/v1/leaderboards/community/?community_id=42&limit=10&offset=20"
```

### Top Performers by Meals Completed (This Month)

```bash
curl -X GET "http://localhost:8000/api/v1/leaderboards/global/?sort_by=meals&time_period=this_month&limit=20" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Phase 2+ Enhancements

### 1. Redis Caching
- Implement `LeaderboardCacheConfig` TTL rules
- Cache by `(leaderboard_type, trait_id, community_id, time_period, sort_by, offset, limit)`
- Invalidate on coin/badge/meal updates

### 2. Timestamped Metrics
- Add `created_at` to `meal_history`, `challenge_results` collections
- Replace date_joined filter with actual metric timestamps
- Enable accurate period-based filtering

### 3. Trend Analysis
- Add `rank_history` tracking (daily snapshots)
- Endpoint: `GET /leaderboards/trends/?user_id=X&days=30`

### 4. Search & Filter
- `GET /leaderboards/global/?username_contains=ali` — substring search
- `GET /leaderboards/global/?min_coins=1000&max_coins=5000` — range filters

### 5. Real-Time Updates (WebSocket)
- Subscribe to leaderboard changes
- Broadcast rank shifts when coins/badges awarded

---

## Files Modified / Created

| File | Status |
|------|--------|
| `gamification/models/leaderboard.py` | ✅ Created |
| `gamification/services/hybrid_leaderboard_service.py` | ✅ Created |
| `admin_api/views/hybrid_leaderboard_views.py` | ✅ Created |
| `admin_api/urls.py` | ✅ Updated |

---

## Testing Checklist

- ✅ Global leaderboard returns ranked users (sorted by coins)
- ✅ Trait leaderboard filters by top_sifats
- ✅ Community leaderboard filters by community_id
- ✅ Time period filtering works (this_week, this_month, all_time)
- ✅ Sorting by badges/meals/accuracy works
- ✅ Pagination (limit/offset) works
- ✅ User rank calculation correct
- ✅ Missing required params return 400
- ✅ Invalid community_id/trait_id return 400
- ✅ Unauthenticated requests return 401
- ✅ Large limit capped at 1000
- ✅ Negative offset converted to 0
- ✅ All endpoints return JSON in expected format

---

## Summary

**Hybrid Leaderboards** completes Phase 6 Gamification with 4 queryable endpoints supporting:
- 3 leaderboard types (global, trait, community)
- 4 sorting metrics (coins, badges, meals, accuracy)
- 3 time periods (all_time, this_month, this_week)
- Pagination (limit, offset)
- User rank lookup
- Extensible architecture for caching & trends

Ready for Phase 2 enhancement: Redis caching, timestamped metrics, trend analysis, and real-time WebSocket updates.
