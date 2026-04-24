"""
admin_api/views/leaderboard_trend_views.py
==========================================
Leaderboard trend analysis API endpoints.

Endpoints:
  GET  /api/v1/leaderboards/trend/user/{user_id} - User's rank trend
  GET  /api/v1/leaderboards/trending - Trending users (most improved, most active)
  GET  /api/v1/leaderboards/stats - Overall leaderboard statistics
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth, _require_admin
from gamification.services.leaderboard_trend_service import (
    LeaderboardTrendService, TrendError, TrendNotFoundError
)

log = logging.getLogger(__name__)

_VALID_TREND_METRICS = frozenset({'rank_improvement', 'coins_gained', 'badges_unlocked', 'momentum'})


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Return error JSON response"""
    return JsonResponse({"detail": message}, status=status)


# ═══════════════════════════════════════════════════════════════════════════════
# ── User Trend ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class UserTrendView(View):
    """
    GET /api/v1/leaderboards/trend/user/{user_id}?leaderboard_type=global&days=30

    Get user's rank trend over time (30 days default).
    Shows how user's rank changed, coins gained, badges unlocked.
    """

    def get(self, request, user_id: int):
        try:
            token_user_id = _require_auth(request)
            if token_user_id != user_id:
                return _json_error("Access denied.", status=403)

            # Parse parameters
            _qp = request.GET
            _qpget = _qp.get
            leaderboard_type = _qpget("leaderboard_type", "global").strip()
            trait_id = _qpget("trait_id", "").strip() or None
            community_id_str = _qpget("community_id", "").strip()

            try:
                days = int(_qpget("days", 30))
                days = min(max(days, 1), 90)  # Clamp 1-90 days
            except ValueError:
                days = 30

            # Parse community_id
            community_id = None
            if community_id_str:
                try:
                    community_id = int(community_id_str)
                except ValueError:
                    return _json_error("Invalid community_id", status=400)

            # Get user trend
            trend_response = LeaderboardTrendService.get_user_trend(
                user_id=user_id,
                leaderboard_type=leaderboard_type,
                trait_id=trait_id,
                community_id=community_id,
                days=days,
            )

            # Format trend data
            trend_data = [
                {
                    "snapshot_date": point.snapshot_date.isoformat(),
                    "rank": point.rank,
                    "coins_earned": point.coins_earned,
                    "platinum_badges": point.platinum_badges,
                    "gold_and_above": point.gold_and_above,
                    "meals_completed": point.meals_completed,
                    "challenges_won": point.challenges_won,
                    "avg_accuracy": point.avg_accuracy,
                }
                for point in trend_response.trend_data
            ]

            return JsonResponse({
                "user_id": trend_response.user_id,
                "username": trend_response.username,
                "leaderboard_type": trend_response.leaderboard_type,
                "trait_id": trend_response.trait_id,
                "community_id": trend_response.community_id,
                "current_rank": trend_response.current_rank,
                "current_coins": trend_response.current_coins,
                "current_badges": trend_response.current_badges,
                "trend_days": trend_response.trend_days,
                "rank_change": trend_response.rank_change,
                "coins_gained": trend_response.coins_gained,
                "badges_unlocked": trend_response.badges_unlocked,
                "trend_data": trend_data,
            })

        except TrendNotFoundError:
            return _json_error("No trend data found.", status=404)
        except TrendError:
            return _json_error("Trend processing error.", status=400)
        except PermissionError as e:
            return _json_error(str(e), status=403)
        except Exception as e:
            log.error(f"UserTrendView error: {e}", exc_info=True)
            return _json_error("Internal server error.", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Trending Users ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class TrendingUsersView(View):
    """
    GET /api/v1/leaderboards/trending?metric=rank_improvement&days=7&limit=10

    Get trending users (most improved, most active, etc).

    Metrics:
      - rank_improvement: Most improved ranks (negative = better)
      - coins_gained: Most coins earned
      - badges_unlocked: Most badges gained
      - momentum: Ascending/stable/descending momentum
    """

    def get(self, request):
        try:
            # Require authentication
            _require_auth(request)

            # Parse parameters
            _qp = request.GET
            _qpget = _qp.get
            leaderboard_type = _qpget("leaderboard_type", "global").strip()
            metric = _qpget("metric", "rank_improvement").strip()

            try:
                days = int(_qpget("days", 7))
                days = min(max(days, 1), 90)
            except ValueError:
                days = 7

            try:
                limit = int(_qpget("limit", 10))
                limit = min(max(limit, 1), 100)
            except ValueError:
                limit = 10

            # Validate metric
            if metric not in _VALID_TREND_METRICS:
                return _json_error(
                    f"Invalid metric. Must be one of: {', '.join(sorted(_VALID_TREND_METRICS))}",
                    status=400
                )

            # Get trending users
            trending = LeaderboardTrendService.get_trending_users(
                leaderboard_type=leaderboard_type,
                days=days,
                limit=limit,
                metric=metric,
            )

            # Format response (trending is already a list of dicts)
            return JsonResponse({
                "leaderboard_type": leaderboard_type,
                "metric": metric,
                "days": days,
                "limit": limit,
                "count": len(trending),
                "trending_users": trending,
            })

        except TrendError:
            return _json_error("Trend processing error.", status=400)
        except Exception as e:
            log.error(f"TrendingUsersView error: {e}", exc_info=True)
            return _json_error("Internal server error.", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Leaderboard Statistics ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class LeaderboardStatsView(View):
    """
    GET /api/v1/leaderboards/stats?leaderboard_type=global&days=7

    Get overall trend statistics for a leaderboard.

    Returns:
      - most_improved: Top 10 users by rank improvement
      - most_active: Top 10 users by coins earned
      - avg_rank_movement: Average daily rank volatility
    """

    def get(self, request):
        try:
            # Require authentication
            _require_auth(request)

            # Parse parameters
            _qp = request.GET
            _qpget = _qp.get
            leaderboard_type = _qpget("leaderboard_type", "global").strip()

            try:
                days = int(_qpget("days", 7))
                days = min(max(days, 1), 90)
            except ValueError:
                days = 7

            # Get leaderboard stats
            stats = LeaderboardTrendService.get_leaderboard_stats(
                leaderboard_type=leaderboard_type,
                days=days,
            )

            return JsonResponse({
                "leaderboard_type": stats.leaderboard_type,
                "snapshot_count": stats.snapshot_count,
                "days_tracked": stats.days_tracked,
                "avg_rank_movement": stats.avg_rank_movement,
                "most_improved": stats.most_improved,
                "most_active": stats.most_active,
            })

        except TrendError:
            return _json_error("Trend processing error.", status=400)
        except Exception as e:
            log.error(f"LeaderboardStatsView error: {e}", exc_info=True)
            return _json_error("Internal server error.", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Manual Snapshot ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class TakeSnapshotView(View):
    """
    POST /api/v1/leaderboards/snapshot

    Manually take a leaderboard snapshot (normally called by scheduled cron).
    Admin-only endpoint.

    Request body:
      {
        "leaderboard_type": "global",
        "trait_id": null,
        "community_id": null,
        "time_period": "all_time",
        "sort_by": "coins",
        "top_n": 100
      }
    """

    def post(self, request):
        try:
            _require_admin(request)

            body = json.loads(request.body.decode())
            _bget = body.get

            leaderboard_type = _bget("leaderboard_type", "global")
            trait_id = _bget("trait_id", None)
            community_id = _bget("community_id", None)
            time_period = _bget("time_period", "all_time")
            sort_by = _bget("sort_by", "coins")
            try:
                top_n = min(max(int(_bget("top_n", 100)), 10), 500)
            except (ValueError, TypeError):
                top_n = 100

            # Take snapshot
            snapshot_id = LeaderboardTrendService.take_snapshot(
                leaderboard_type=leaderboard_type,
                trait_id=trait_id,
                community_id=community_id,
                time_period=time_period,
                sort_by=sort_by,
                top_n=top_n,
            )

            return JsonResponse({
                "snapshot_id": snapshot_id,
                "status": "success",
                "message": f"Snapshot taken for {leaderboard_type} leaderboard",
            })

        except ValueError:
            return _json_error("Unauthorized.", status=401)
        except PermissionError:
            return _json_error("Admin access required.", status=403)
        except TrendError:
            return _json_error("Trend processing error.", status=400)
        except json.JSONDecodeError:
            return _json_error("Invalid JSON body", status=400)
        except Exception as e:
            log.error(f"TakeSnapshotView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Cleanup Old Snapshots ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CleanupSnapshotsView(View):
    """
    POST /api/v1/leaderboards/cleanup

    Delete old snapshots (older than 90 days).
    Admin-only endpoint, normally called by scheduled cron.
    """

    def post(self, request):
        try:
            _require_admin(request)

            # Cleanup
            deleted_count = LeaderboardTrendService.cleanup_old_snapshots()

            return JsonResponse({
                "status": "success",
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} old snapshots",
            })

        except ValueError:
            return _json_error("Unauthorized.", status=401)
        except PermissionError:
            return _json_error("Admin access required.", status=403)
        except TrendError:
            return _json_error("Trend processing error.", status=400)
        except Exception as e:
            log.error(f"CleanupSnapshotsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
