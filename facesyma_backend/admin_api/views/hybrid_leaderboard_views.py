"""
admin_api/views/hybrid_leaderboard_views.py
==========================================
Hybrid leaderboard API endpoints: global, trait-based, community-specific.

Endpoints:
  GET  /api/v1/leaderboards - Get leaderboard (hybrid dispatcher)
  GET  /api/v1/leaderboards/global - Global leaderboard
  GET  /api/v1/leaderboards/trait - Trait-based leaderboard
  GET  /api/v1/leaderboards/community - Community leaderboard
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from gamification.models.leaderboard import LeaderboardFilter
from gamification.services.hybrid_leaderboard_service import (
    HybridLeaderboardService, LeaderboardError
)

log = logging.getLogger(__name__)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Return error JSON response"""
    return JsonResponse({"detail": message}, status=status)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Hybrid Leaderboard (Dispatcher) ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class HybridLeaderboardView(View):
    """
    GET /api/v1/leaderboards?leaderboard_type=global&time_period=all_time&sort_by=coins&limit=100&offset=0

    Get leaderboard based on filter (hybrid dispatcher).
    Supports: global, trait, community leaderboards.
    """

    def get(self, request):
        try:
            # Get optional user_id for rank calculation
            user_id = _require_auth(request)

            # Parse query parameters
            leaderboard_type = request.GET.get("leaderboard_type", "global").strip()
            trait_id = request.GET.get("trait_id", "").strip() or None
            community_id_str = request.GET.get("community_id", "").strip()
            time_period = request.GET.get("time_period", "all_time").strip()
            sort_by = request.GET.get("sort_by", "coins").strip()

            # Parse limit
            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            # Parse offset
            try:
                offset = int(request.GET.get("offset", 0))
                offset = max(offset, 0)
            except ValueError:
                offset = 0

            # Parse community_id
            community_id = None
            if community_id_str:
                try:
                    community_id = int(community_id_str)
                except ValueError:
                    return _json_error("Invalid community_id", status=400)

            # Build filter
            filter_params = LeaderboardFilter(
                leaderboard_type=leaderboard_type,
                trait_id=trait_id,
                community_id=community_id,
                time_period=time_period,
                sort_by=sort_by,
                limit=limit,
                offset=offset,
            )

            # Get leaderboard
            leaderboard = HybridLeaderboardService.get_hybrid_leaderboard(
                filter_params=filter_params,
                user_id=user_id,
            )

            # Format response
            entries_data = [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "username": e.username,
                    "avatar": e.avatar,
                    "coins_balance": e.coins_balance,
                    "total_coins_earned": e.total_coins_earned,
                    "platinum_badges": e.platinum_badges,
                    "gold_and_above": e.gold_and_above,
                    "meals_completed": e.meals_completed,
                    "challenges_won": e.challenges_won,
                    "avg_accuracy": e.avg_accuracy,
                    "top_traits": e.top_traits,
                }
                for e in leaderboard.entries
            ]

            return JsonResponse({
                "leaderboard_type": leaderboard.leaderboard_type,
                "leaderboard_name": leaderboard.leaderboard_name,
                "time_period": leaderboard.time_period,
                "sort_by": leaderboard.sort_by,
                "total_entries": leaderboard.total_entries,
                "user_rank": leaderboard.user_rank,
                "cached": leaderboard.cached,
                "cache_expiry": leaderboard.cache_expiry.isoformat() if leaderboard.cache_expiry else None,
                "entries": entries_data,
            })

        except LeaderboardError as e:
            return _json_error(f"Leaderboard error: {str(e)}", status=400)
        except ValueError as e:
            return _json_error(f"Invalid parameter: {str(e)}", status=400)
        except Exception as e:
            log.error(f"HybridLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Global Leaderboard ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class GlobalLeaderboardView(View):
    """
    GET /api/v1/leaderboards/global?time_period=all_time&sort_by=coins&limit=100&offset=0

    Get global leaderboard (all users ranked).
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)

            # Parse parameters
            time_period = request.GET.get("time_period", "all_time").strip()
            sort_by = request.GET.get("sort_by", "coins").strip()

            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            try:
                offset = int(request.GET.get("offset", 0))
                offset = max(offset, 0)
            except ValueError:
                offset = 0

            # Get leaderboard
            leaderboard = HybridLeaderboardService.get_global_leaderboard(
                time_period=time_period,
                sort_by=sort_by,
                limit=limit,
                offset=offset,
                user_id=user_id,
            )

            # Format response
            entries_data = [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "username": e.username,
                    "avatar": e.avatar,
                    "coins_balance": e.coins_balance,
                    "total_coins_earned": e.total_coins_earned,
                    "platinum_badges": e.platinum_badges,
                    "gold_and_above": e.gold_and_above,
                    "meals_completed": e.meals_completed,
                    "challenges_won": e.challenges_won,
                    "avg_accuracy": e.avg_accuracy,
                    "top_traits": e.top_traits,
                }
                for e in leaderboard.entries
            ]

            return JsonResponse({
                "leaderboard_type": "global",
                "leaderboard_name": "Global Leaderboard",
                "time_period": time_period,
                "sort_by": sort_by,
                "total_entries": leaderboard.total_entries,
                "user_rank": leaderboard.user_rank,
                "entries": entries_data,
            })

        except LeaderboardError as e:
            return _json_error(f"Leaderboard error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"GlobalLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Trait-Based Leaderboard ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class TraitLeaderboardView(View):
    """
    GET /api/v1/leaderboards/trait?trait_id=dürüst&time_period=all_time&sort_by=coins&limit=100&offset=0

    Get trait-based leaderboard (users with specific sıfat).
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)

            # Parse parameters
            trait_id = request.GET.get("trait_id", "").strip()
            if not trait_id:
                return _json_error("Missing trait_id", status=400)

            time_period = request.GET.get("time_period", "all_time").strip()
            sort_by = request.GET.get("sort_by", "coins").strip()

            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            try:
                offset = int(request.GET.get("offset", 0))
                offset = max(offset, 0)
            except ValueError:
                offset = 0

            # Get leaderboard
            leaderboard = HybridLeaderboardService.get_trait_leaderboard(
                trait_id=trait_id,
                time_period=time_period,
                sort_by=sort_by,
                limit=limit,
                offset=offset,
                user_id=user_id,
            )

            # Format response
            entries_data = [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "username": e.username,
                    "avatar": e.avatar,
                    "coins_balance": e.coins_balance,
                    "total_coins_earned": e.total_coins_earned,
                    "platinum_badges": e.platinum_badges,
                    "gold_and_above": e.gold_and_above,
                    "meals_completed": e.meals_completed,
                    "challenges_won": e.challenges_won,
                    "avg_accuracy": e.avg_accuracy,
                    "top_traits": e.top_traits,
                }
                for e in leaderboard.entries
            ]

            return JsonResponse({
                "leaderboard_type": "trait",
                "leaderboard_name": f"Trait-Based: {trait_id}",
                "trait_id": trait_id,
                "time_period": time_period,
                "sort_by": sort_by,
                "total_entries": leaderboard.total_entries,
                "user_rank": leaderboard.user_rank,
                "entries": entries_data,
            })

        except LeaderboardError as e:
            return _json_error(f"Leaderboard error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"TraitLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Community Leaderboard ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CommunityLeaderboardView(View):
    """
    GET /api/v1/leaderboards/community?community_id=123&time_period=all_time&sort_by=coins&limit=100&offset=0

    Get community-specific leaderboard.
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)

            # Parse parameters
            community_id_str = request.GET.get("community_id", "").strip()
            if not community_id_str:
                return _json_error("Missing community_id", status=400)

            try:
                community_id = int(community_id_str)
            except ValueError:
                return _json_error("Invalid community_id", status=400)

            time_period = request.GET.get("time_period", "all_time").strip()
            sort_by = request.GET.get("sort_by", "coins").strip()

            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            try:
                offset = int(request.GET.get("offset", 0))
                offset = max(offset, 0)
            except ValueError:
                offset = 0

            # Get leaderboard
            leaderboard = HybridLeaderboardService.get_community_leaderboard(
                community_id=community_id,
                time_period=time_period,
                sort_by=sort_by,
                limit=limit,
                offset=offset,
                user_id=user_id,
            )

            # Format response
            entries_data = [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "username": e.username,
                    "avatar": e.avatar,
                    "coins_balance": e.coins_balance,
                    "total_coins_earned": e.total_coins_earned,
                    "platinum_badges": e.platinum_badges,
                    "gold_and_above": e.gold_and_above,
                    "meals_completed": e.meals_completed,
                    "challenges_won": e.challenges_won,
                    "avg_accuracy": e.avg_accuracy,
                    "top_traits": e.top_traits,
                }
                for e in leaderboard.entries
            ]

            return JsonResponse({
                "leaderboard_type": "community",
                "leaderboard_name": f"Community #{community_id}",
                "community_id": community_id,
                "time_period": time_period,
                "sort_by": sort_by,
                "total_entries": leaderboard.total_entries,
                "user_rank": leaderboard.user_rank,
                "entries": entries_data,
            })

        except LeaderboardError as e:
            return _json_error(f"Leaderboard error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"CommunityLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
