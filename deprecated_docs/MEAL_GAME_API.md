# Meal Game API Documentation

## Overview

Meal Game is a weekly gamification feature where users select meals from rotating countries and guess if those meals match their personality traits (sıfats). Each week features a different country's cuisine, and users earn coins through selections and correct guesses.

## Architecture

### Services
- **MealService** (`facesyma_ai/diet_coaching/services/meal_service.py`)
  - Loads meal data from JSON files (18 countries)
  - Manages meal selection and sıfat guessing
  - Calculates weekly leaderboards
  - Tracks user meal history

### Models
- **Meal** (`facesyma_ai/diet_coaching/models/meal.py`)
  - Core meal entity with nutrition info, dietary preferences, sıfat appeal
  - MealSelection: MongoDB document schema for selections
  - MealLeaderboardEntry: Leaderboard ranking data

### Views
- **Meal Views** (`facesyma_backend/admin_api/views/meal_views.py`)
  - HTTP endpoints for all meal game operations

### Database
- **MongoDB Collections**
  - `meal_selections`: Stores user selections and sıfat guesses
  - Indexes created by `create_meal_indexes()`

## API Endpoints

All endpoints are prefixed with `/api/v1/`

### 1. GET /meals/daily
**Get today's 3 meals for the current rotation week**

Returns the meals for this week's featured country (rotates every 7 days through 18 countries).

**Response:**
```json
{
    "country": "japan",
    "week_key": "2026-W17",
    "meals": [
        {
            "id": "jp_breakfast_001",
            "name_en": "Miso Soup",
            "name_tr": "Miso Soup",
            "description": "Traditional Japanese soup with miso paste...",
            "nutrition": {
                "calories": 180,
                "protein": 8,
                "carbs": 12,
                "fat": 6
            },
            "prep_time_min": 15,
            "dietary": {
                "omnivore": true,
                "vegetarian": true,
                "vegan": false,
                "gluten_free": true
            },
            "sifat_appeal": ["rahat", "saglikli"],
            "season": "year_round",
            "frequency_weight": 0.95
        },
        ...
    ]
}
```

---

### 2. POST /meals/select
**User selects a meal and earns coins**

Records the meal selection in MongoDB and awards 10 coins to the user.

**Request:**
```json
{
    "meal_id": "jp_breakfast_001",
    "country": "japan"
}
```

**Response:**
```json
{
    "success": true,
    "coins_earned": 10,
    "new_balance": 150,
    "transaction_id": "tn_1234567890",
    "meal_name": "Miso Soup"
}
```

**Notes:**
- Requires authentication (user_id from auth token)
- Automatically integrates with CoinService
- Selection recorded with timestamp and week_key for leaderboard tracking

---

### 3. POST /meals/guess-sifat
**User guesses if meal matches their personality**

MVP uses simple heuristic: 70% chance the guess is "correct". On correct guess, awards 5 bonus coins.

**Request:**
```json
{
    "meal_id": "jp_breakfast_001",
    "country": "japan",
    "guess": "yes"  // or "no" / "unsure"
}
```

**Response:**
```json
{
    "is_correct": true,
    "bonus_coins": 5,
    "feedback": "✓ Correct! This meal appeals to rahat, saglikli personalities.",
    "new_balance": 155
}
```

**Guess Values:**
- `"yes"` — User thinks meal matches their personality
- `"no"` — User thinks meal doesn't match
- `"unsure"` — User uncertain (no bonus coins possible)

**MVP Logic:**
- 70% of guesses evaluate as "correct" (randomized)
- Correct guesses award 5 bonus coins
- Updates MongoDB selection record with guess + correctness

---

### 4. GET /meals/leaderboard
**Get this week's meal game leaderboard for a country**

Ranks users by meals_completed (primary), then coins_earned (secondary). Includes accuracy percentage for sıfat guesses.

**Query Parameters:**
- `country` (optional): Country name (e.g., "japan"). Defaults to current week's featured country
- `limit` (optional): Max results, default 100, clamped to 1-1000

**Example Request:**
```
GET /meals/leaderboard?country=japan&limit=50
```

**Response:**
```json
{
    "week_key": "2026-W17",
    "country": "japan",
    "entries": [
        {
            "rank": 1,
            "user_id": 123,
            "username": "duygucu_user",
            "avatar": "https://...",
            "meals_completed": 15,
            "coins_earned": 150,
            "accuracy_percent": 73.3
        },
        {
            "rank": 2,
            "user_id": 456,
            "username": "deniz_fan",
            "avatar": "https://...",
            "meals_completed": 14,
            "coins_earned": 140,
            "accuracy_percent": 64.2
        },
        ...
    ]
}
```

**Ranking Formula:**
- Primary: `meals_completed DESC`
- Secondary: `coins_earned DESC`
- Accuracy: `(correct_guesses / total_guesses) * 100`

---

### 5. GET /meals/history
**Get user's meal selection history (paginated)**

Returns all meals the user has selected, newest first. Includes their sıfat guesses and coin earnings.

**Query Parameters:**
- `limit` (optional): Max results per page, default 50, clamped to 1-500
- `offset` (optional): Skip N results for pagination, default 0

**Example Request:**
```
GET /meals/history?limit=50&offset=0
```

**Response:**
```json
{
    "total": 42,
    "limit": 50,
    "offset": 0,
    "entries": [
        {
            "_id": "507f1f77bcf86cd799439011",
            "meal_id": "jp_breakfast_001",
            "meal_name_en": "Miso Soup",
            "country": "japan",
            "selected_at": "2026-04-19T14:30:00",
            "sifat_guess": "yes",
            "sifat_correct": true,
            "coins_earned": 15
        },
        ...
    ]
}
```

---

## Weekly Country Rotation

Countries rotate in this order (18-week cycle):

1. Japan
2. Turkey
3. China
4. India
5. Italy
6. Greece
7. Germany
8. France
9. Korea
10. Portugal
11. Bangladesh
12. Indonesia
13. Pakistan
14. Thailand
15. Malaysia
16. Mexico
17. Vietnam
18. Philippines

**Current Week Determination:**
```python
from datetime import datetime
now = datetime.utcnow()
week_of_year = now.isocalendar()[1]  # 1-53
country_index = (week_of_year - 1) % 18
country = WEEK_ROTATION[country_index]
```

---

## Database Schema

### meal_selections Collection

```json
{
    "_id": ObjectId,
    "user_id": 123,
    "meal_id": "jp_breakfast_001",
    "meal_name_en": "Miso Soup",
    "meal_name_tr": "Miso Soup",
    "country": "japan",
    "selected_at": "2026-04-19T14:30:00Z",
    "week_key": "2026-W17",
    "sifat_guess": "yes",
    "sifat_correct": true,
    "coins_earned": 15
}
```

### Indexes

| Collection | Indexes |
|---|---|
| `meal_selections` | `(user_id, week_key)` — leaderboard ranking |
| `meal_selections` | `(country, week_key)` — weekly filtering |
| `meal_selections` | `(user_id, selected_at DESC)` — user history |
| `meal_selections` | `(selected_at DESC)` — admin reporting |
| `meal_selections` | `(meal_id)` — meal lookup |

---

## Coin Economy

### Earning Mechanisms

| Action | Coins |
|---|---|
| Select a meal | +10 |
| Sıfat guess correct | +5 bonus |

### Integration with CoinService

All coin operations go through `CoinService` with `TransactionType.MEAL_GAME` type:
- Atomic operations via MongoDB
- Full transaction history tracking
- User balance automatically updated

---

## Setup & Deployment

### 1. Initialize Database

Run the migration script once on deployment:

```bash
python manage.py shell < facesyma_backend/migrate_coin_system.py
```

This will:
1. Create `meal_selections` collection
2. Create all required indexes
3. Initialize coin system (if not already done)

### 2. Register URLs

URLs already registered in `facesyma_backend/admin_api/urls.py`:
```python
path('meals/daily/', MealDailyView.as_view(), name='meals-daily'),
path('meals/select/', MealSelectView.as_view(), name='meals-select'),
path('meals/guess-sifat/', MealSifatGuessView.as_view(), name='meals-guess-sifat'),
path('meals/leaderboard/', MealLeaderboardView.as_view(), name='meals-leaderboard'),
path('meals/history/', MealHistoryView.as_view(), name='meals-history'),
```

### 3. Verify Meal JSON Files

Ensure 18 meal JSON files exist in `facesyma_ai/diet_coaching/data/`:
- `meals_ja.json` (Japan)
- `meals_tr.json` (Turkey)
- `meals_zh.json` (China)
- ... (and 15 more)

Each file should contain an array of Meal objects matching the Pydantic schema.

---

## Testing

### Quick Test Workflow

```bash
# 1. Get today's meals
curl http://localhost:8000/api/v1/meals/daily

# 2. Select a meal
curl -X POST http://localhost:8000/api/v1/meals/select \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"meal_id":"jp_breakfast_001","country":"japan"}'

# 3. Guess sıfat match
curl -X POST http://localhost:8000/api/v1/meals/guess-sifat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"meal_id":"jp_breakfast_001","country":"japan","guess":"yes"}'

# 4. View leaderboard
curl http://localhost:8000/api/v1/meals/leaderboard?country=japan&limit=10

# 5. View your history
curl http://localhost:8000/api/v1/meals/history?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Future Enhancements

### MVP → Phase 2
- **Real Sıfat Matching**: Replace 70% heuristic with actual user sıfat profile comparison
- **Streaks**: Track consecutive days of meal selection
- **Badges**: Award specific badges (e.g., "Adventurous Eater", "Sıfat Expert")
- **Notifications**: Push notifications for leaderboard position changes

### Integration Points
- **Social Challenges**: Use meal selections for social multi-player challenges
- **Community Missions**: Aggregate meal selections across user communities
- **Trait Discovery**: Meal selections inform user sıfat assessments

---

## Error Handling

All endpoints return standard error responses:

```json
{
    "detail": "Error message describing the issue"
}
```

| Status | Reason |
|---|---|
| 400 | Missing required fields, invalid country, invalid guess value |
| 401 | User not authenticated |
| 404 | Meal not found, country not found |
| 500 | Server error |

---

## Performance Considerations

- **Meal Caching**: All meals loaded into memory once per process (persists for request lifecycle)
- **Index Efficiency**: Leaderboard aggregation uses indexed fields (`country`, `week_key`)
- **Pagination**: All list endpoints support pagination to limit response size
- **MongoDB Atomicity**: Selection + coin award are atomic transactions

---

## Related Documentation

- [Coin System API](COIN_SYSTEM_API.md)
- [Meal Game Service](facesyma_ai/diet_coaching/services/meal_service.py)
- [Meal Models](facesyma_ai/diet_coaching/models/meal.py)
