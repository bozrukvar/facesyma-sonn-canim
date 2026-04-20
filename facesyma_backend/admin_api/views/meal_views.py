"""
admin_api/views/meal_views.py
===========================
Meal game API endpoints: daily meals, selection, sifat guesses, leaderboard.

Endpoints:
  GET  /api/v1/meals/daily - Get today's meals for current rotation week
  POST /api/v1/meals/select - User selects a meal
  POST /api/v1/meals/guess-sifat - User guesses sifat match
  GET  /api/v1/meals/leaderboard - Weekly leaderboard for current country
  GET  /api/v1/meals/history - User's meal selection history
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from diet_coaching.models.meal import (
    Meal, MealSelectionRequest, MealSifatGuessRequest, MealLeaderboardEntry
)
from diet_coaching.services.meal_service import (
    MealService, MealError, MealNotFoundError, InvalidCountryError
)

log = logging.getLogger(__name__)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Return error JSON response"""
    return JsonResponse({"detail": message}, status=status)


def _json(request) -> dict:
    """Parse JSON request body"""
    try:
        return json.loads(request.body)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# ── Daily Meals ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MealDailyView(View):
    """
    GET /api/v1/meals/daily

    Returns today's 3 meals for the current week's country rotation.

    Response:
    {
        "country": "japan",
        "week_key": "2026-W17",
        "meals": [
            {
                "id": "jp_breakfast_001",
                "name_en": "Miso Soup",
                "name_tr": "Miso Soup",
                "description": "...",
                "nutrition": {...},
                "prep_time_min": 15,
                "sifat_appeal": ["rahat", "saglikli"],
                "season": "year_round",
                "frequency_weight": 0.95
            },
            ...
        ]
    }
    """

    def get(self, request):
        try:
            # Get current week's country
            country = MealService.get_current_week_country()

            # Load all meals for this country
            meals = MealService.load_meals(country)

            # Select 3 random meals
            selected = MealService.select_random_meals(meals, count=3)

            # Serialize to dict
            meals_data = [
                {
                    "id": meal.id,
                    "name_en": meal.name_en,
                    "name_tr": meal.name_tr,
                    "description": meal.description,
                    "nutrition": {
                        "calories": meal.nutrition.calories,
                        "protein": meal.nutrition.protein,
                        "carbs": meal.nutrition.carbs,
                        "fat": meal.nutrition.fat,
                    },
                    "prep_time_min": meal.prep_time_min,
                    "dietary": {
                        "omnivore": meal.dietary.omnivore,
                        "vegetarian": meal.dietary.vegetarian,
                        "vegan": meal.dietary.vegan,
                        "gluten_free": meal.dietary.gluten_free,
                    },
                    "sifat_appeal": meal.sifat_appeal,
                    "season": meal.season,
                    "frequency_weight": meal.frequency_weight,
                }
                for meal in selected
            ]

            return JsonResponse({
                "country": country,
                "week_key": MealService._get_week_key(),
                "meals": meals_data,
            })

        except InvalidCountryError as e:
            return _json_error(f"Country error: {str(e)}", status=404)
        except MealError as e:
            return _json_error(f"Meal error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"MealDailyView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Meal Selection ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MealSelectView(View):
    """
    POST /api/v1/meals/select

    User selects a meal. Records selection and awards coins.

    Request:
    {
        "meal_id": "jp_breakfast_001",
        "country": "japan"
    }

    Response:
    {
        "success": true,
        "coins_earned": 10,
        "new_balance": 150,
        "transaction_id": "tn_1234567890",
        "meal_name": "Miso Soup"
    }
    """

    def post(self, request):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Parse request
            body = _json(request)
            meal_id = body.get("meal_id", "").strip()
            country = body.get("country", "").strip()

            if not meal_id or not country:
                return _json_error("Missing meal_id or country", status=400)

            # Select meal
            new_balance, trans_id = MealService.select_meal(
                user_id=user_id,
                meal_id=meal_id,
                country=country,
            )

            # Get meal name for response
            meals = MealService.load_meals(country)
            meal = next((m for m in meals if m.id == meal_id), None)
            meal_name = meal.name_en if meal else "Unknown"

            return JsonResponse({
                "success": True,
                "coins_earned": 10,
                "new_balance": new_balance,
                "transaction_id": trans_id,
                "meal_name": meal_name,
            })

        except MealNotFoundError as e:
            return _json_error(f"Meal not found: {str(e)}", status=404)
        except InvalidCountryError as e:
            return _json_error(f"Country error: {str(e)}", status=404)
        except MealError as e:
            return _json_error(f"Meal error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"MealSelectView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Sifat Guess ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MealSifatGuessView(View):
    """
    POST /api/v1/meals/guess-sifat

    User guesses if meal matches their personality.

    Request:
    {
        "meal_id": "jp_breakfast_001",
        "country": "japan",
        "guess": "yes"  # "yes", "no", or "unsure"
    }

    Response:
    {
        "is_correct": true,
        "bonus_coins": 5,
        "feedback": "✓ Correct! This meal appeals to rahat, saglikli personalities.",
        "new_balance": 155
    }
    """

    def post(self, request):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Parse request
            body = _json(request)
            meal_id = body.get("meal_id", "").strip()
            country = body.get("country", "").strip()
            guess = body.get("guess", "").strip().lower()

            if not meal_id or not country:
                return _json_error("Missing meal_id or country", status=400)

            if guess not in ["yes", "no", "unsure"]:
                return _json_error("Invalid guess; must be 'yes', 'no', or 'unsure'", status=400)

            # Record guess
            is_correct, bonus, feedback = MealService.guess_sifat_match(
                user_id=user_id,
                meal_id=meal_id,
                country=country,
                guess=guess,
            )

            # Get new balance
            from core.services.coin_service import CoinService
            new_balance = CoinService.get_balance(user_id)

            return JsonResponse({
                "is_correct": is_correct,
                "bonus_coins": bonus,
                "feedback": feedback,
                "new_balance": new_balance,
            })

        except MealNotFoundError as e:
            return _json_error(f"Meal not found: {str(e)}", status=404)
        except InvalidCountryError as e:
            return _json_error(f"Country error: {str(e)}", status=404)
        except MealError as e:
            return _json_error(f"Meal error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"MealSifatGuessView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Weekly Leaderboard ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MealLeaderboardView(View):
    """
    GET /api/v1/meals/leaderboard?country=japan&limit=100

    Returns this week's meal game leaderboard for a country.

    Query Parameters:
    - country: Country name (e.g., "japan") — defaults to current rotation week's country
    - limit: Max results (default 100)

    Response:
    {
        "week_key": "2026-W17",
        "country": "japan",
        "entries": [
            {
                "rank": 1,
                "user_id": 123,
                "username": "user_123",
                "avatar": "https://...",
                "meals_completed": 15,
                "coins_earned": 150,
                "accuracy_percent": 73.3
            },
            ...
        ]
    }
    """

    def get(self, request):
        try:
            # Get country from query params, default to current week
            country = request.GET.get("country", "").strip()
            if not country:
                country = MealService.get_current_week_country()

            # Validate country
            from diet_coaching.models.meal import COUNTRY_CODES
            if country not in COUNTRY_CODES:
                return _json_error(
                    f"Invalid country: {country}. Valid countries: {list(COUNTRY_CODES.keys())}",
                    status=400
                )

            # Get limit from query params
            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)  # Clamp to 1-1000
            except ValueError:
                limit = 100

            # Get leaderboard
            entries = MealService.get_weekly_leaderboard(
                country=country,
                limit=limit,
            )

            # Serialize entries
            entries_data = [
                {
                    "rank": entry.rank,
                    "user_id": entry.user_id,
                    "username": entry.username,
                    "avatar": entry.avatar,
                    "meals_completed": entry.meals_completed,
                    "coins_earned": entry.coins_earned,
                    "accuracy_percent": entry.accuracy_percent,
                }
                for entry in entries
            ]

            return JsonResponse({
                "week_key": MealService._get_week_key(),
                "country": country,
                "entries": entries_data,
            })

        except InvalidCountryError as e:
            return _json_error(f"Country error: {str(e)}", status=404)
        except MealError as e:
            return _json_error(f"Meal error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"MealLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── User Meal History ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MealHistoryView(View):
    """
    GET /api/v1/meals/history?limit=50&offset=0

    Returns user's meal selection history.

    Query Parameters:
    - limit: Max results (default 50)
    - offset: Skip N results (default 0)

    Response:
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
    """

    def get(self, request):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Get pagination params
            try:
                limit = int(request.GET.get("limit", 50))
                offset = int(request.GET.get("offset", 0))
                limit = min(max(limit, 1), 500)  # Clamp to 1-500
                offset = max(offset, 0)
            except ValueError:
                limit = 50
                offset = 0

            # Get history
            docs, total = MealService.get_user_meal_history(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )

            return JsonResponse({
                "total": total,
                "limit": limit,
                "offset": offset,
                "entries": docs,
            })

        except Exception as e:
            log.error(f"MealHistoryView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
