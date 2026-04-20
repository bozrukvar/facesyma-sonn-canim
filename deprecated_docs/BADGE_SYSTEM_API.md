# Badge/Rozet System API Documentation

## Overview

The Badge System provides visual progression and achievement recognition across all gamification activities. Users unlock badges in 4 tiers (Bronze → Silver → Gold → Platinum) by completing activities and reaching milestones. Each tier unlock awards bonus coins.

## Architecture

### Models
- **BadgeDefinition** (`gamification/models/badge.py`)
  - Badge template with unlock conditions and tier thresholds
- **UserBadge**: User's progress on a specific badge
- **BadgeTier**: Tier level with threshold requirement
- **BadgeLeaderboardEntry**: Ranking by badges

### Services
- **BadgeService** (`gamification/services/badge_service.py`)
  - Progress tracking
  - Automatic tier unlocks
  - Leaderboard queries
  - Coin rewards

### Views
- **Badge Views** (`admin_api/views/badge_views.py`)
  - 4 HTTP endpoints for badge operations

### Database
- **MongoDB**: User badges stored in `user.badges` document array
- Automatic unlock detection on badge progress update

## Badge Types & Tiers

### 4-Level Tier System

Every badge has 4 progressive tiers:

```
BRONZE (Tier 1)      → 25 coins
    ↓
SILVER (Tier 2)      → 50 coins (25 base + 25 bonus)
    ↓
GOLD (Tier 3)        → 75 coins (25 base + 50 bonus)
    ↓
PLATINUM (Tier 4)    → 100 coins (25 base + 75 bonus)
```

Each tier unlock awards `coin_reward_per_tier` coins (typically 25-50 coins per tier).

### Predefined Badges (8)

#### Meal Game Badges (4)

1. **Adventurous Eater** (`meal_adventurous_eater`)
   - Unlock condition: Country count
   - Bronze: 10 countries | Silver: 20 | Gold: 50 | Platinum: 100
   - Category: Exploration

2. **Sıfat Expert** (`meal_sifat_expert`)
   - Unlock condition: Accuracy percentage
   - Bronze: 70% | Silver: 80% | Gold: 90% | Platinum: 95%
   - Category: Mastery

3. **Streak Master** (`meal_streak_master`)
   - Unlock condition: Consecutive days
   - Bronze: 7 days | Silver: 14 | Gold: 30 | Platinum: 100
   - Category: Consistency

4. **Leaderboard Champion** (`meal_leaderboard_champion`)
   - Unlock condition: Weekly leaderboard placement
   - Bronze: Top 10 | Silver: Top 5 | Gold: Top 3 | Platinum: 1st place
   - Category: Social

#### Challenge Badges (2)

5. **Competitor** (`challenge_competitor`)
   - Unlock condition: Challenges completed
   - Bronze: 5 | Silver: 10 | Gold: 25 | Platinum: 50

6. **Challenge Winner** (`challenge_winner`)
   - Unlock condition: 1st place finishes
   - Bronze: 3 wins | Silver: 10 | Gold: 25 | Platinum: 50

#### Coaching & Quest Badges (2)

7. **Dedicated Learner** (`coaching_dedicated`)
   - Unlock condition: Modules completed
   - Bronze: 10 | Silver: 25 | Gold: 50 | Platinum: 100

8. **Quest Master** (`quest_master`)
   - Unlock condition: Daily quests completed
   - Bronze: 30 | Silver: 60 | Gold: 100 | Platinum: 365

## API Endpoints

All endpoints are prefixed with `/api/v1/`

### 1. GET /badges
**Get all badge definitions (templates)**

Returns all available badges with tier thresholds (no user progress).

**Response:**
```json
{
    "count": 8,
    "badges": [
        {
            "badge_id": "meal_adventurous_eater",
            "name_en": "Adventurous Eater",
            "name_tr": "Macera Arayıcı Yiyici",
            "description_en": "Select meals from different countries",
            "description_tr": "Farklı ülkelerden yemek seç",
            "game_type": "meal",
            "category": "exploration",
            "icon_url": "https://...",
            "unlock_condition": "count",
            "tiers": [
                {
                    "tier": "bronze",
                    "level": 1,
                    "threshold": 10
                },
                {
                    "tier": "silver",
                    "level": 2,
                    "threshold": 20
                },
                {
                    "tier": "gold",
                    "level": 3,
                    "threshold": 50
                },
                {
                    "tier": "platinum",
                    "level": 4,
                    "threshold": 100
                }
            ],
            "coin_reward_per_tier": 25
        },
        ...
    ]
}
```

---

### 2. GET /badges/user
**Get user's badge collection with progress**

Returns all badges with user's current progress, unlocked tiers, and coin earnings.

**Response:**
```json
{
    "user_id": 123,
    "total_badges": 8,
    "platinum_badges": 2,
    "gold_and_above": 5,
    "badges": [
        {
            "badge_id": "meal_adventurous_eater",
            "current_tier": "silver",
            "current_progress": 23,
            "unlocked_at": "2026-04-19T10:30:00Z",
            "tier_unlocks": {
                "bronze": "2026-04-19T10:30:00Z",
                "silver": "2026-04-19T14:15:00Z"
            },
            "total_coins_earned": 50
        },
        {
            "badge_id": "meal_sifat_expert",
            "current_tier": "gold",
            "current_progress": 91,
            "unlocked_at": "2026-04-18T09:00:00Z",
            "tier_unlocks": {
                "bronze": "2026-04-18T09:00:00Z",
                "silver": "2026-04-18T15:30:00Z",
                "gold": "2026-04-19T12:45:00Z"
            },
            "total_coins_earned": 75
        },
        ...
    ]
}
```

**Stats Included:**
- `total_badges`: All badges user has progress on (8 total available)
- `platinum_badges`: Count of badges at Platinum tier
- `gold_and_above`: Count at Gold or Platinum tier

---

### 3. GET /badges/:badge_id
**Get specific badge definition with user progress**

Returns badge template with optional user progress (if authenticated).

**Response:**
```json
{
    "badge_id": "meal_adventurous_eater",
    "name_en": "Adventurous Eater",
    "name_tr": "Macera Arayıcı Yiyici",
    "description_en": "Select meals from different countries",
    "description_tr": "Farklı ülkelerden yemek seç",
    "game_type": "meal",
    "category": "exploration",
    "icon_url": "https://...",
    "unlock_condition": "count",
    "tiers": [
        {
            "tier": "bronze",
            "level": 1,
            "threshold": 10
        },
        ...
    ],
    "coin_reward_per_tier": 25,
    "user_progress": {
        "current_tier": "silver",
        "current_progress": 23,
        "next_threshold": 50
    }
}
```

**Notes:**
- `user_progress`: Only included if user authenticated (null otherwise)
- `next_threshold`: Target for next tier unlock

---

### 4. GET /badges/:badge_id/leaderboard
**Get leaderboard for a specific badge**

Ranks users by platinum badge count or progress on specific badge.

**Query Parameters:**
- `metric` (optional): `"platinum_count"` (default) or `"current_progress"`
- `limit` (optional): Max results, default 100, clamped to 1-1000

**Example Request:**
```
GET /badges/meal_adventurous_eater/leaderboard?metric=current_progress&limit=20
```

**Response:**
```json
{
    "badge_id": "meal_adventurous_eater",
    "metric": "current_progress",
    "entries": [
        {
            "rank": 1,
            "user_id": 456,
            "username": "user_456",
            "avatar": "https://...",
            "current_tier": "platinum",
            "current_progress": 127,
            "platinum_count": 5
        },
        {
            "rank": 2,
            "user_id": 789,
            "username": "user_789",
            "avatar": "https://...",
            "current_tier": "gold",
            "current_progress": 87,
            "platinum_count": 3
        },
        ...
    ]
}
```

---

## Badge Progress Tracking

### Automatic Updates

Badges are updated automatically when users complete activities:

```python
# When user selects meal:
BadgeService.update_badge_progress(
    user_id=user_id,
    badge_id="meal_adventurous_eater",
    delta=1  # +1 country
)
# Checks if 10 countries reached → unlocks bronze
# Checks if 20 countries reached → unlocks silver
# Etc.
```

### Unlock Detection

When progress exceeds tier threshold:
1. **Tier marked as unlocked** with timestamp
2. **Coins awarded** via atomic CoinService transaction
3. **Current tier updated** to reflect highest unlocked
4. **Event recorded** for notifications

### Coin Awards

Each tier unlock awards `coin_reward_per_tier` coins:

```
Bronze unlock:    +25 coins
Silver unlock:    +25 coins (now at 50 total)
Gold unlock:      +25 coins (now at 75 total)
Platinum unlock:  +25 coins (now at 100 total)
```

**Max per badge**: 100 coins (if all 4 tiers unlocked)
**Max across all badges**: 800 coins (8 badges × 100 coins)

---

## Integration Points

### Meal Game
```python
# When user selects from new country:
BadgeService.update_badge_progress(
    user_id=user_id,
    badge_id="meal_adventurous_eater",
    delta=1
)

# When user completes sifat guess:
if accuracy >= 70:
    BadgeService.update_badge_progress(
        user_id=user_id,
        badge_id="meal_sifat_expert",
        delta=accuracy  # e.g., delta=87 for 87% accuracy
    )

# Weekly leaderboard update:
if user_rank == 1:
    BadgeService.update_badge_progress(
        user_id=user_id,
        badge_id="meal_leaderboard_champion",
        delta=1
    )
```

### Social Challenges
```python
# When user completes challenge:
BadgeService.update_badge_progress(
    user_id=user_id,
    badge_id="challenge_competitor",
    delta=1
)

# When user wins challenge:
if placement == 1:
    BadgeService.update_badge_progress(
        user_id=user_id,
        badge_id="challenge_winner",
        delta=1
    )
```

### Coaching
```python
# When user completes coaching module:
BadgeService.update_badge_progress(
    user_id=user_id,
    badge_id="coaching_dedicated",
    delta=1
)
```

### Daily Quests
```python
# When user completes daily quest:
BadgeService.update_badge_progress(
    user_id=user_id,
    badge_id="quest_master",
    delta=1
)
```

---

## Database Schema

### User Document (appfaceapi_myuser)

Badges stored in user document:

```json
{
    "id": 123,
    "username": "user_123",
    "badges": {
        "meal_adventurous_eater": {
            "badge_id": "meal_adventurous_eater",
            "current_tier": "silver",
            "current_progress": 23,
            "unlocked_at": "2026-04-19T10:30:00Z",
            "tier_unlocks": {
                "bronze": "2026-04-19T10:30:00Z",
                "silver": "2026-04-19T14:15:00Z"
            },
            "total_coins_earned": 50
        },
        "meal_sifat_expert": {...},
        ...
    }
}
```

### Badge Definitions

Stored in Python `BADGE_DEFINITIONS` dict (in-memory, not MongoDB):

```python
BADGE_DEFINITIONS = {
    "meal_adventurous_eater": BadgeDefinition(...),
    "meal_sifat_expert": BadgeDefinition(...),
    ...
}
```

---

## Coin Economy

### Total Possible Earnings

- **Per badge**: 100 coins (25 × 4 tiers)
- **8 badges**: 800 coins
- **Other sources**: Meals (10+5), Challenges (placement bonuses), Quests
- **Total possible**: 800+ coins from badges alone

### Transaction Recording

All badge tier unlocks recorded in `coin_transactions`:

```json
{
    "user_id": 123,
    "amount": 25,
    "type": "badge_unlock",
    "description": "Badge tier unlock: meal_adventurous_eater (silver)",
    "metadata": {
        "badge_id": "meal_adventurous_eater",
        "tier": "silver",
        "threshold": 20
    },
    "created_at": "2026-04-19T14:15:00Z"
}
```

---

## Testing Workflow

### Get All Badges
```bash
curl http://localhost:8000/api/v1/badges
```

### Get User's Badges
```bash
curl http://localhost:8000/api/v1/badges/user \
  -H "Authorization: Bearer TOKEN"
```

### Get Specific Badge
```bash
curl http://localhost:8000/api/v1/badges/meal_adventurous_eater \
  -H "Authorization: Bearer TOKEN"
```

### Get Badge Leaderboard
```bash
curl http://localhost:8000/api/v1/badges/meal_sifat_expert/leaderboard?metric=current_progress&limit=10
```

---

## UI Display Guide

### Badge Card (Profile/Collection View)

```
┌─────────────────────────────┐
│  🍴 Adventurous Eater       │
│  [████░░░░░░░░░░░░░░] 23/50 │ ← Progress bar
│  Current: Silver            │
│  Coins earned: 50           │
│  Next: Gold (50 countries)  │
└─────────────────────────────┘
```

### Badge Progress Bar

Show 4 segments, fill on tier unlock:

```
Bronze ✓ | Silver ✓ | Gold □ | Platinum □
```

### Badge Tier Icons

```
🥉 Bronze   🥈 Silver   🥇 Gold   👑 Platinum
```

### Leaderboard Display

```
1. user_456 - ⭐⭐⭐⭐⭐ (5 platinum badges)
2. user_789 - ⭐⭐⭐ (3 platinum badges)
3. user_123 - ⭐⭐ (2 platinum badges)
```

---

## MVP → Phase 2 Enhancements

### Immediate Features
- ✓ 4-tier progression (Bronze → Platinum)
- ✓ 8 badge types across game categories
- ✓ Automatic unlock detection
- ✓ Tier-based coin rewards
- ✓ Leaderboards (platinum count + progress)

### Phase 2 Additions
- **Badge Events**: Notifications on unlock
- **Badge Showcase**: Featured badges in profile
- **Seasonal Badges**: Limited-time badges
- **Badge Collections**: Special badge sets (e.g., "All Meal Badges")
- **Badge Mastery**: Harder tier targets for advanced users
- **Social Display**: Show badges on leaderboards/profiles

---

## Error Handling

All endpoints return standard error responses:

```json
{
    "detail": "Error message"
}
```

| Status | Reason |
|--------|--------|
| 400 | Invalid request, bad metric |
| 401 | User not authenticated |
| 404 | Badge not found |
| 500 | Server error |

---

## Performance Notes

- **In-memory definitions**: Badge templates loaded once
- **Embedded documents**: User badges stored in user document (no joins)
- **Atomic updates**: Progress updates via MongoDB `$inc` operator
- **Leaderboard queries**: Full scan (8 badges × active users) — acceptable MVP
- **Future optimization**: Redis cache for leaderboard queries

---

## Related Documentation

- [Coin System API](COIN_SYSTEM_API.md)
- [Meal Game API](MEAL_GAME_API.md)
- [Social Challenges API](SOCIAL_CHALLENGES_API.md)
