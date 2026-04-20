# Social Challenges API Documentation

## Overview

Social Challenges enable users to compete with friends and the community in time-limited competitions. Features include:
- **Live Scoring**: Real-time leaderboard updates as users complete activities
- **Hybrid Leaderboards**: Mixed views of friends + public rankings
- **Optional Handicapping**: Difficulty adjustment for fair competition
- **Cancellation Penalties**: Small coin penalty for early exit to encourage commitment
- **Push Notifications**: Alerts on rank changes and challenge milestones

## Approved Design Decisions

Based on user requirements (2026-04-19):

1. ✓ **Live Scoring Visible**: Leaderboard updates in real-time as users earn points
2. ✓ **Mixed Leaderboard Mode**: Hybrid display of friends and public rankings
3. ✓ **Optional Handicapping**: Users can select difficulty levels (1-5) for fair play
4. ✓ **Cancellation Penalty**: 2 coins deducted if user exits challenge early
5. ✓ **Push Notifications**: Real-time alerts on rank changes and status updates

## Architecture

### Models
- **SocialChallenge** (`gamification/models/challenge.py`)
  - Challenge document schema with participants, scoring, time limits
- **ChallengeParticipant**: Individual participant with score, rank, handicap
- **ChallengeLeaderboardEntry**: Ranking display model
- **ChallengeType**: Predefined challenge templates

### Services
- **ChallengeService** (`gamification/services/challenge_service.py`)
  - Full challenge lifecycle management
  - Live score updates with ranking recalculation
  - Leaderboard queries respecting visibility modes
  - Notification coordination

### Views
- **Challenge Views** (`admin_api/views/challenge_views.py`)
  - 7 HTTP endpoints for challenge operations

### Database
- **MongoDB Collections**
  - `social_challenges`: Challenge documents with participants
  - Indexes for fast leaderboard queries and participant lookup

## Challenge Types

4 predefined challenge types (customizable):

| Type ID | Name | Category | Duration | Base Reward | Metric |
|---------|------|----------|----------|-------------|--------|
| `meal_selection` | Meal Selection | Social | 24h | 50 coins | Count |
| `personality_match` | Personality Match | Discovery | 24h | 75 coins | Accuracy |
| `coaching_streak` | Coaching Streak | Coaching | 7d | 100 coins | Count |
| `daily_quest` | Daily Quest | Activity | 24h | 60 coins | Count |

Create custom types by extending `CHALLENGE_TYPES` dict.

## API Endpoints

All endpoints are prefixed with `/api/v1/`

### 1. GET /challenges/types
**Get all available challenge types**

Returns list of challenge types users can create.

**Response:**
```json
{
    "count": 4,
    "types": [
        {
            "type_id": "meal_selection",
            "name_en": "Meal Selection Challenge",
            "name_tr": "Yemek Seçim Yarışması",
            "description_en": "Select the most meals in a day",
            "description_tr": "Bir gün içinde en çok yemek seç",
            "category": "social",
            "duration_minutes": 1440,
            "coin_reward_base": 50,
            "leaderboard_metric": "count"
        },
        ...
    ]
}
```

---

### 2. POST /challenges/create
**Create a new social challenge**

Creator automatically joins as participant. Can set visibility (friends-only or public), leaderboard mode, and optional handicapping.

**Request:**
```json
{
    "type_id": "meal_selection",
    "title": "Weekend Meal Challenge",
    "description": "Select meals together!",
    "visibility": "public",
    "leaderboard_mode": "mixed",
    "is_handicapped": false,
    "duration_minutes": 1440
}
```

**Response:**
```json
{
    "success": true,
    "challenge_id": "ch_jp4k8d2l",
    "title": "Weekend Meal Challenge",
    "start_time": "2026-04-19T14:30:00Z",
    "end_time": "2026-04-20T14:30:00Z",
    "participants_count": 1
}
```

**Fields:**
- `type_id`: (required) Challenge type ID
- `title`: (required) Display name for challenge
- `description`: (required) Challenge description
- `visibility`: (required) `"friends_only"` or `"public"`
- `leaderboard_mode`: (required) `"friends"`, `"public"`, or `"mixed"`
- `is_handicapped`: (optional, default false) Enable difficulty levels
- `duration_minutes`: (optional, default 1440) 5-1440 minutes (5 min to 24 hours)

---

### 3. POST /challenges/join
**Join an existing challenge**

User joins challenge and can optionally select difficulty handicap if enabled.

**Request:**
```json
{
    "challenge_id": "ch_jp4k8d2l",
    "handicap_level": 2
}
```

**Response:**
```json
{
    "success": true,
    "challenge_id": "ch_jp4k8d2l",
    "joined_at": "2026-04-19T14:30:00Z",
    "participants_count": 25
}
```

**Notes:**
- `handicap_level`: (optional) 1-5 if `is_handicapped=true` on challenge (1=easier, 5=harder)
- User cannot join if already a participant

---

### 4. POST /challenges/update-score
**Update user's score in challenge (live scoring)**

Used when activities (meal selections, quest completions) happen. Automatically recalculates ranking.

**Request:**
```json
{
    "challenge_id": "ch_jp4k8d2l",
    "score_delta": 10,
    "metadata": {"meal_id": "jp_breakfast_001", "meal_name": "Miso Soup"}
}
```

**Response:**
```json
{
    "success": true,
    "challenge_id": "ch_jp4k8d2l",
    "new_score": 42,
    "current_rank": 3
}
```

**Features:**
- `score_delta`: (required) Points to add/subtract (can be negative)
- `metadata`: (optional) Context data for notifications
- **Live Leaderboard**: Rank recalculated immediately and visible to all participants
- **Notifications**: Triggers rank change alerts

---

### 5. GET /challenges/leaderboard
**Get leaderboard for a challenge**

Respects leaderboard mode (friends/public/mixed) and returns ranked participants.

**Query Parameters:**
- `challenge_id` (required): Challenge ID
- `limit` (optional): Max results, default 100, clamped to 1-1000

**Example Request:**
```
GET /challenges/leaderboard?challenge_id=ch_jp4k8d2l&limit=50
```

**Response:**
```json
{
    "challenge_id": "ch_jp4k8d2l",
    "entries": [
        {
            "rank": 1,
            "user_id": 456,
            "username": "user_456",
            "avatar": "https://...",
            "score": 450,
            "handicap_level": null
        },
        {
            "rank": 2,
            "user_id": 123,
            "username": "user_123",
            "avatar": "https://...",
            "score": 420,
            "handicap_level": 2
        },
        ...
    ]
}
```

**Ranking:**
- Primary: Score (descending)
- Secondary: Join time (ascending)
- Only active (non-cancelled) participants shown

---

### 6. POST /challenges/cancel
**User exits/cancels a challenge**

Marks user as inactive and applies cancellation penalty (2 coins).

**Request:**
```json
{
    "challenge_id": "ch_jp4k8d2l",
    "reason": "No longer interested"
}
```

**Response:**
```json
{
    "success": true,
    "challenge_id": "ch_jp4k8d2l",
    "penalty_coins": 2
}
```

**Design Decision: Cancellation Penalty**
- Penalty: 2 coins deducted via CoinService
- Prevents abandonment mid-competition
- User removed from leaderboard (marked inactive)
- Challenge record preserved for history

---

### 7. GET /challenges/active
**Get user's active and upcoming challenges**

Returns all challenges user participates in with pending/active status.

**Query Parameters:**
- `limit` (optional): Max results, default 50, clamped to 1-500

**Example Request:**
```
GET /challenges/active?limit=10
```

**Response:**
```json
{
    "total": 3,
    "challenges": [
        {
            "challenge_id": "ch_jp4k8d2l",
            "type_id": "meal_selection",
            "title": "Weekend Meal Challenge",
            "status": "active",
            "participants_count": 25,
            "user_rank": 3,
            "user_score": 42,
            "end_time": "2026-04-20T14:30:00Z"
        },
        {
            "challenge_id": "ch_kl9m3p2x",
            "type_id": "coaching_streak",
            "title": "Weekly Coaching Challenge",
            "status": "pending",
            "participants_count": 12,
            "user_rank": 5,
            "user_score": 28,
            "end_time": "2026-04-26T14:30:00Z"
        },
        ...
    ]
}
```

## Design Principles

### 1. Live Scoring ✓
- Score updates immediately via `update-score` endpoint
- Rank recalculation is atomic
- Leaderboard reflects real-time state

### 2. Mixed Leaderboard Mode ✓
- `"mixed"` mode shows hybrid view:
  - Friends appear at top (if friend relationship defined)
  - Public leaderboard follows
  - Current user always visible
- Supports social competition

### 3. Handicapping ✓
- Optional difficulty levels (1-5)
- Tracks in participant document
- Displayed on leaderboard for fairness transparency
- Allows balanced competition between new/experienced users

### 4. Cancellation Penalty ✓
- 2 coins deducted via atomic `CoinService.deduct_coins()`
- Penalty recorded in transaction history
- Encourages commitment without being prohibitive

### 5. Notifications ✓
- Triggered on:
  - Challenge creation/start
  - User rank improvement
  - New top score
  - Challenge ending soon (5 min warning)
  - Challenge completion
- Supports future push notification service

## Database Schema

### social_challenges Collection

```json
{
    "_id": ObjectId,
    "challenge_id": "ch_jp4k8d2l",
    "type_id": "meal_selection",
    "creator_id": 123,
    "title": "Weekend Meal Challenge",
    "description": "Select meals together!",
    "visibility": "public",
    "status": "active",
    "participants": [
        {
            "user_id": 456,
            "username": "user_456",
            "avatar": "https://...",
            "score": 450,
            "rank": 1,
            "handicap_level": null,
            "joined_at": "2026-04-19T14:30:00Z",
            "cancelled_at": null,
            "is_active": true
        },
        ...
    ],
    "leaderboard_mode": "mixed",
    "is_handicapped": false,
    "cancellation_penalty": 2,
    "start_time": "2026-04-19T14:30:00Z",
    "end_time": "2026-04-20T14:30:00Z",
    "created_at": "2026-04-19T14:30:00Z",
    "updated_at": "2026-04-19T14:30:00Z",
    "metadata": {
        "estimated_participants": 25,
        "total_score": 15240,
        "duration_minutes": 1440,
        "coin_reward_base": 50
    }
}
```

### Indexes

| Index | Purpose |
|-------|---------|
| `challenge_id UNIQUE` | Quick challenge lookup |
| `status` | Find active/pending challenges |
| `creator_id, created_at DESC` | Creator's challenges |
| `start_time, end_time` | Time-based queries |
| `participants.user_id` | Find user's challenges |
| `visibility, status` | Filter public/friends-only |

## Coin Economy

### Earning Mechanics

Challenge-related earnings go through `CoinService` with `TransactionType.CHALLENGE_WIN` / `CHALLENGE_LOSS`.

**Completion Rewards** (Placement Bonuses):
- 1st place: 150% of base reward
- 2nd place: 125% of base reward
- 3rd place: 110% of base reward
- 4th+: 100% of base reward

**Example:**
- `meal_selection`: Base 50 coins
- 1st place winner: 75 coins (50 × 1.5)
- 2nd place: 62 coins (50 × 1.25)

### Spending Mechanics

- **Cancellation Penalty**: 2 coins deducted (recorded as `CHALLENGE_LOSS`)
- **Entry Stake** (future): Optional coin entry fee

## Workflow Examples

### Create and Join a Challenge

```bash
# 1. Get challenge types
curl http://localhost:8000/api/v1/challenges/types

# 2. Create challenge
curl -X POST http://localhost:8000/api/v1/challenges/create \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type_id": "meal_selection",
    "title": "Friends Meal Challenge",
    "description": "See who can select the most meals!",
    "visibility": "friends_only",
    "leaderboard_mode": "mixed",
    "is_handicapped": false,
    "duration_minutes": 1440
  }'
# Response: {"challenge_id": "ch_xyz..."}

# 3. Friend joins
curl -X POST http://localhost:8000/api/v1/challenges/join \
  -H "Authorization: Bearer FRIEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": "ch_xyz..."}'

# 4. View live leaderboard
curl http://localhost:8000/api/v1/challenges/leaderboard?challenge_id=ch_xyz...

# 5. Update score (when meal selected)
curl -X POST http://localhost:8000/api/v1/challenges/update-score \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "ch_xyz...",
    "score_delta": 1,
    "metadata": {"meal_id": "jp_breakfast_001"}
  }'

# 6. Check ranking
curl http://localhost:8000/api/v1/challenges/leaderboard?challenge_id=ch_xyz...

# 7. Cancel if needed
curl -X POST http://localhost:8000/api/v1/challenges/cancel \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"challenge_id": "ch_xyz...", "reason": "Too busy"}'
```

## Integration Points

### With Meal Game
```python
# When user selects meal in meal game:
# 1. Awards 10 coins via CoinService
# 2. Also updates any active meal_selection challenges
ChallengeService.update_score(
    challenge_id=challenge_id,
    user_id=user_id,
    score_delta=1,
    metadata={"meal_id": meal_id, "meal_name": meal_name}
)
```

### With Coaching System
```python
# When user completes coaching:
# 1. Awards coaching coins
# 2. Updates any active coaching_streak challenges
ChallengeService.update_score(
    challenge_id=challenge_id,
    user_id=user_id,
    score_delta=duration_minutes,
    metadata={"module": module_name}
)
```

### With Daily Quests
```python
# When user completes daily quest:
# 1. Awards quest coins
# 2. Updates any active daily_quest challenges
ChallengeService.update_score(
    challenge_id=challenge_id,
    user_id=user_id,
    score_delta=1,
    metadata={"quest_id": quest_id}
)
```

## MVP → Phase 2 Enhancements

### Immediate Needs
- ✓ Live scoring with real-time ranking
- ✓ Mixed leaderboard mode
- ✓ Cancellation penalties
- ✓ Handicapping system
- ✓ Notification triggers

### Phase 2 Additions
- **Friend Relationships**: Filter leaderboard by actual friend list
- **Challenge Templates**: Pre-built challenge configurations
- **Team Challenges**: Multi-user teams competing
- **Seasonal Challenges**: Recurring weekly/monthly challenges
- **Challenge Analytics**: User performance tracking
- **Challenge Discovery**: Browse public challenges

## Error Handling

All endpoints return standard error responses:

```json
{
    "detail": "Error message describing the issue"
}
```

| Status | Reason |
|--------|--------|
| 400 | Invalid request, missing fields, bad type |
| 401 | User not authenticated |
| 404 | Challenge not found |
| 500 | Server error |

## Performance Considerations

- **Index Coverage**: All leaderboard queries use indexes
- **Atomic Updates**: Score updates are atomic, no race conditions
- **Pagination**: Leaderboard supports limit for large competitions
- **Caching**: Future: Redis cache for frequent leaderboard queries
- **Scalability**: MongoDB handles 1000+ participants per challenge

## Related Documentation

- [Coin System API](COIN_SYSTEM_API.md)
- [Meal Game API](MEAL_GAME_API.md)
- [Gamification Architecture](GAMIFICATION_DESIGN.md)
