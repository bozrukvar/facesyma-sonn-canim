"""
admin_api/views/badge_views.py
=============================
Badge/Rozet API endpoints: collection, progress, leaderboards.

Endpoints:
  GET  /api/v1/badges - Get all badge definitions
  GET  /api/v1/badges/user - Get user's badges with progress
  GET  /api/v1/badges/:badge_id - Get specific badge definition
  GET  /api/v1/badges/:badge_id/leaderboard - Badge leaderboard
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from gamification.models.badge import BADGE_DEFINITIONS
from gamification.services.badge_service import (
    BadgeService, BadgeError, BadgeNotFoundError
)

log = logging.getLogger(__name__)

_VALID_BADGE_METRICS   = frozenset({'platinum_count', 'gold_count', 'silver_count', 'bronze_count', 'total_count'})
_GOLD_AND_ABOVE_TIERS  = frozenset({'gold', 'platinum'})


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Return error JSON response"""
    return JsonResponse({"detail": message}, status=status)


# ═══════════════════════════════════════════════════════════════════════════════
# ── All Badges ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class BadgesListView(View):
    """
    GET /api/v1/badges

    Get all badge definitions (templates).

    Response:
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
                "unlock_condition": "count",
                "tiers": [
                    {"tier": "bronze", "level": 1, "threshold": 10},
                    ...
                ]
            },
            ...
        ]
    }
    """

    def get(self, request):
        try:
            badges = BadgeService.list_all_badges()

            badges_data = [
                {
                    "badge_id": b.badge_id,
                    "name_en": b.name_en,
                    "name_tr": b.name_tr,
                    "description_en": b.description_en,
                    "description_tr": b.description_tr,
                    "game_type": b.game_type,
                    "category": b.category,
                    "icon_url": b.icon_url,
                    "unlock_condition": b.unlock_condition,
                    "tiers": [
                        {
                            "tier": t.tier,
                            "level": t.level,
                            "threshold": t.threshold,
                        }
                        for t in b.tiers
                    ],
                    "coin_reward_per_tier": b.coin_reward_per_tier,
                }
                for b in badges
            ]

            return JsonResponse({
                "count": len(badges_data),
                "badges": badges_data,
            })

        except Exception as e:
            log.error(f"BadgesListView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── User Badges ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserBadgesView(View):
    """
    GET /api/v1/badges/user

    Get user's badge collection with current progress.

    Response:
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

            # Get user's badges
            badges_dict = BadgeService.get_user_badges(user_id=user_id)

            # Calculate stats
            _vals = badges_dict.values()
            platinum_count = len([
                b for b in _vals
                if b.get("current_tier") == "platinum"
            ])
            gold_and_above = len([
                b for b in _vals
                if b.get("current_tier") in _GOLD_AND_ABOVE_TIERS
            ])

            badges_data = [
                {
                    "badge_id": b["badge_id"],
                    "current_tier": b["current_tier"],
                    "current_progress": b["current_progress"],
                    "unlocked_at": b["unlocked_at"],
                    "tier_unlocks": b["tier_unlocks"],
                    "total_coins_earned": b["total_coins_earned"],
                }
                for b in _vals
            ]

            return JsonResponse({
                "user_id": user_id,
                "total_badges": len(badges_data),
                "platinum_badges": platinum_count,
                "gold_and_above": gold_and_above,
                "badges": badges_data,
            })

        except BadgeError as e:
            return _json_error("Badge error.", status=400)
        except Exception as e:
            log.error(f"UserBadgesView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Badge Detail ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class BadgeDetailView(View):
    """
    GET /api/v1/badges/:badge_id

    Get specific badge definition (for detail modal).

    Response:
    {
        "badge_id": "meal_adventurous_eater",
        "name_en": "Adventurous Eater",
        "name_tr": "Macera Arayıcı Yiyici",
        "description_en": "Select meals from different countries",
        ...
        "tiers": [...],
        "user_progress": {
            "current_tier": "silver",
            "current_progress": 23,
            "next_threshold": 50
        }
    }
    """

    def get(self, request, badge_id):
        try:
            # Get badge definition
            badge_def = BadgeService.get_badge_definition(badge_id)

            # Get optional user progress
            user_id = _require_auth(request)
            user_progress = None

            if user_id:
                badges_dict = BadgeService.get_user_badges(user_id=user_id)
                if badge_id in badges_dict:
                    user_badge = badges_dict[badge_id]
                    _ubget = user_badge.get
                    current_tier = _ubget("current_tier")
                    current_progress = _ubget("current_progress", 0)

                    # Find next threshold
                    next_threshold = None
                    for tier in badge_def.tiers:
                        _tt = tier.threshold
                        if (
                            current_tier is None or
                            _tt > current_progress
                        ):
                            next_threshold = _tt
                            break

                    user_progress = {
                        "current_tier": current_tier,
                        "current_progress": current_progress,
                        "next_threshold": next_threshold,
                    }

            response_data = {
                "badge_id": badge_def.badge_id,
                "name_en": badge_def.name_en,
                "name_tr": badge_def.name_tr,
                "description_en": badge_def.description_en,
                "description_tr": badge_def.description_tr,
                "game_type": badge_def.game_type,
                "category": badge_def.category,
                "icon_url": badge_def.icon_url,
                "unlock_condition": badge_def.unlock_condition,
                "tiers": [
                    {
                        "tier": t.tier,
                        "level": t.level,
                        "threshold": t.threshold,
                    }
                    for t in badge_def.tiers
                ],
                "coin_reward_per_tier": badge_def.coin_reward_per_tier,
                "user_progress": user_progress,
            }

            return JsonResponse(response_data)

        except BadgeNotFoundError as e:
            return _json_error("Badge not found.", status=404)
        except BadgeError as e:
            return _json_error("Badge error.", status=400)
        except Exception as e:
            log.error(f"BadgeDetailView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Badge Leaderboard ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class BadgeLeaderboardView(View):
    """
    GET /api/v1/badges/:badge_id/leaderboard?metric=platinum_count&limit=50

    Get leaderboard for specific badge.

    Query Parameters:
    - metric: "platinum_count", "current_progress" (default: platinum_count)
    - limit: Max results (default 100, max 1000)

    Response:
    {
        "badge_id": "meal_adventurous_eater",
        "metric": "platinum_count",
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
            ...
        ]
    }
    """

    def get(self, request, badge_id):
        try:
            # Get metric and limit from query params
            _qget = request.GET.get
            metric = _qget("metric", "platinum_count")
            if metric not in _VALID_BADGE_METRICS:
                metric = "platinum_count"
            try:
                limit = int(_qget("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            # Get leaderboard
            entries = BadgeService.get_badge_leaderboard(
                badge_id=badge_id,
                metric=metric,
                limit=limit,
            )

            # Serialize entries
            entries_data = [
                {
                    "rank": entry.rank,
                    "user_id": entry.user_id,
                    "username": entry.username,
                    "avatar": entry.avatar,
                    "current_tier": entry.current_tier,
                    "current_progress": entry.current_progress,
                    "platinum_count": entry.platinum_count,
                }
                for entry in entries
            ]

            return JsonResponse({
                "badge_id": badge_id,
                "metric": metric,
                "entries": entries_data,
            })

        except BadgeNotFoundError:
            return _json_error("Badge not found.", status=404)
        except BadgeError:
            return _json_error("Badge processing error.", status=400)
        except Exception as e:
            log.error(f"BadgeLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error.", status=500)
