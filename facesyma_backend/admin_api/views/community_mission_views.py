"""
admin_api/views/community_mission_views.py
=========================================
Community missions API endpoints: list, join, contribute, progress.

Endpoints:
  GET  /api/v1/missions/types - List mission types
  GET  /api/v1/missions/active - List active missions
  POST /api/v1/missions/join - Join a mission
  POST /api/v1/missions/contribute - Contribute to progress
  GET  /api/v1/missions/:mission_id - Get mission details
  GET  /api/v1/missions/:mission_id/leaderboard - Contribution leaderboard
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from gamification.models.community_mission import MISSION_TYPES
from gamification.services.community_mission_service import (
    CommunityMissionService, MissionError, MissionNotFoundError,
    MissionTypeNotFoundError, UserAlreadyJoinedError
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
# ── Mission Types ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MissionTypesView(View):
    """
    GET /api/v1/missions/types

    Get all available mission types.
    """

    def get(self, request):
        try:
            types_data = [
                {
                    "mission_type_id": t.mission_type_id,
                    "name_en": t.name_en,
                    "name_tr": t.name_tr,
                    "description_en": t.description_en,
                    "description_tr": t.description_tr,
                    "category": t.category,
                    "duration_days": t.duration_days,
                    "target_value": t.target_value,
                    "unit": t.unit,
                    "coin_reward_per_person": t.coin_reward_per_person,
                    "difficulty": t.difficulty,
                }
                for t in MISSION_TYPES.values()
            ]

            return JsonResponse({
                "count": len(types_data),
                "types": types_data,
            })

        except Exception as e:
            log.error(f"MissionTypesView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Active Missions ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ActiveMissionsView(View):
    """
    GET /api/v1/missions/active?community_id=123&limit=10

    Get active missions for a community (or global).
    """

    def get(self, request):
        try:
            # Get optional community_id
            try:
                community_id = int(request.GET.get("community_id")) if request.GET.get("community_id") else None
            except ValueError:
                community_id = None

            # Get limit
            try:
                limit = int(request.GET.get("limit", 50))
                limit = min(max(limit, 1), 500)
            except ValueError:
                limit = 50

            # Get missions
            missions = CommunityMissionService.get_active_missions(
                community_id=community_id,
                limit=limit,
            )

            # Format response
            missions_data = [
                {
                    "mission_id": m["mission_id"],
                    "title": m["title"],
                    "description": m["description"],
                    "category": m["type_id"].split("_")[0],
                    "current_progress": m["current_progress"],
                    "target_progress": m["target_progress"],
                    "progress_percent": m["progress_percent"],
                    "participants_count": len(m.get("participants", [])),
                    "coin_reward": m["coin_reward_per_person"],
                    "end_date": m["end_date"],
                    "status": m["status"],
                }
                for m in missions
            ]

            return JsonResponse({
                "total": len(missions_data),
                "missions": missions_data,
            })

        except Exception as e:
            log.error(f"ActiveMissionsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Join Mission ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class JoinMissionView(View):
    """
    POST /api/v1/missions/join

    User joins a community mission.
    """

    def post(self, request):
        try:
            # Authenticate
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            username = f"user_{user_id}"
            avatar = None

            # Parse request
            body = _json(request)
            mission_id = body.get("mission_id", "").strip()

            if not mission_id:
                return _json_error("Missing mission_id", status=400)

            # Join mission
            CommunityMissionService.join_mission(
                mission_id=mission_id,
                user_id=user_id,
                username=username,
                avatar=avatar,
            )

            # Get updated mission
            mission = CommunityMissionService.get_mission(mission_id)

            return JsonResponse({
                "success": True,
                "mission_id": mission_id,
                "participants_count": len(mission.get("participants", [])),
                "message": "Joined mission successfully!",
            })

        except MissionNotFoundError as e:
            return _json_error(f"Mission not found: {str(e)}", status=404)
        except UserAlreadyJoinedError as e:
            return _json_error(f"Already joined: {str(e)}", status=400)
        except MissionError as e:
            return _json_error(f"Mission error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"JoinMissionView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Contribute to Mission ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ContributeMissionView(View):
    """
    POST /api/v1/missions/contribute

    User contributes to mission progress.
    """

    def post(self, request):
        try:
            # Authenticate
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Parse request
            body = _json(request)
            mission_id = body.get("mission_id", "").strip()
            contribution = body.get("contribution", 0)
            metadata = body.get("metadata", {})

            if not mission_id or not isinstance(contribution, int) or contribution <= 0:
                return _json_error("Invalid mission_id or contribution", status=400)

            # Contribute
            new_progress, progress_percent = CommunityMissionService.contribute(
                mission_id=mission_id,
                user_id=user_id,
                contribution=contribution,
                metadata=metadata,
            )

            return JsonResponse({
                "success": True,
                "mission_id": mission_id,
                "contribution": contribution,
                "new_progress": new_progress,
                "progress_percent": round(progress_percent, 1),
            })

        except MissionNotFoundError as e:
            return _json_error(f"Mission not found: {str(e)}", status=404)
        except MissionError as e:
            return _json_error(f"Mission error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"ContributeMissionView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Mission Details ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MissionDetailsView(View):
    """
    GET /api/v1/missions/:mission_id

    Get mission details with progress.
    """

    def get(self, request, mission_id):
        try:
            mission = CommunityMissionService.get_mission(mission_id)

            return JsonResponse({
                "mission_id": mission["mission_id"],
                "title": mission["title"],
                "description": mission["description"],
                "status": mission["status"],
                "current_progress": mission["current_progress"],
                "target_progress": mission["target_progress"],
                "progress_percent": mission["progress_percent"],
                "participants_count": len(mission.get("participants", [])),
                "coin_reward_per_person": mission["coin_reward_per_person"],
                "total_coins_distributed": mission["total_coins_distributed"],
                "start_date": mission["start_date"],
                "end_date": mission["end_date"],
                "completed_at": mission.get("completed_at"),
            })

        except MissionNotFoundError as e:
            return _json_error(f"Mission not found: {str(e)}", status=404)
        except Exception as e:
            log.error(f"MissionDetailsView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Mission Leaderboard ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class MissionLeaderboardView(View):
    """
    GET /api/v1/missions/:mission_id/leaderboard?limit=50

    Get contribution leaderboard for a mission.
    """

    def get(self, request, mission_id):
        try:
            # Get limit
            try:
                limit = int(request.GET.get("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            # Get leaderboard
            entries = CommunityMissionService.get_mission_leaderboard(
                mission_id=mission_id,
                limit=limit,
            )

            entries_data = [
                {
                    "rank": e.rank,
                    "user_id": e.user_id,
                    "username": e.username,
                    "avatar": e.avatar,
                    "contribution": e.contribution,
                    "contribution_percent": e.contribution_percent,
                }
                for e in entries
            ]

            return JsonResponse({
                "mission_id": mission_id,
                "entries": entries_data,
            })

        except MissionNotFoundError as e:
            return _json_error(f"Mission not found: {str(e)}", status=404)
        except MissionError as e:
            return _json_error(f"Mission error: {str(e)}", status=400)
        except Exception as e:
            log.error(f"MissionLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
