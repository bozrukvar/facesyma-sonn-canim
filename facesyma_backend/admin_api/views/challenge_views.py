"""
admin_api/views/challenge_views.py
=================================
Social Challenges API endpoints: creation, participation, scoring, leaderboards.

Endpoints:
  POST /api/v1/challenges/create - Create a new challenge
  POST /api/v1/challenges/join - Join an existing challenge
  POST /api/v1/challenges/update-score - Update user score (live)
  GET  /api/v1/challenges/leaderboard - Get challenge leaderboard
  POST /api/v1/challenges/cancel - Exit/cancel a challenge
  GET  /api/v1/challenges/active - Get user's active challenges
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from gamification.models.challenge import (
    CreateChallengeRequest, JoinChallengeRequest, UpdateScoreRequest,
    CancelChallengeRequest, CHALLENGE_TYPES
)
from gamification.services.challenge_service import (
    ChallengeService, ChallengeError, ChallengeNotFoundError,
    InvalidChallengeTypeError, UserAlreadyJoinedError
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
# ── Challenge Types ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeTypesView(View):
    """
    GET /api/v1/challenges/types

    Returns all available challenge types.

    Response:
    {
        "types": [
            {
                "type_id": "meal_selection",
                "name_en": "Meal Selection Challenge",
                "name_tr": "Yemek Seçim Yarışması",
                "description_en": "Select the most meals in a day",
                "description_tr": "Bir gün içinde en çok yemek seç",
                "category": "social",
                "duration_minutes": 1440,
                "coin_reward_base": 50
            },
            ...
        ]
    }
    """

    def get(self, request):
        try:
            types_data = [
                {
                    "type_id": t.type_id,
                    "name_en": t.name_en,
                    "name_tr": t.name_tr,
                    "description_en": t.description_en,
                    "description_tr": t.description_tr,
                    "category": t.category,
                    "duration_minutes": t.duration_minutes,
                    "coin_reward_base": t.coin_reward_base,
                    "leaderboard_metric": t.leaderboard_metric,
                }
                for t in CHALLENGE_TYPES.values()
            ]

            return JsonResponse({
                "count": len(types_data),
                "types": types_data,
            })

        except Exception as e:
            log.error(f"ChallengeTypesView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Create Challenge ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeCreateView(View):
    """
    POST /api/v1/challenges/create

    Create a new social challenge.

    Request:
    {
        "type_id": "meal_selection",
        "title": "Weekend Meal Challenge",
        "description": "Select meals together!",
        "visibility": "public",
        "leaderboard_mode": "mixed",
        "is_handicapped": false,
        "duration_minutes": 1440
    }

    Response:
    {
        "success": true,
        "challenge_id": "ch_jp4k8d2l",
        "title": "Weekend Meal Challenge",
        "start_time": "2026-04-19T14:30:00Z",
        "end_time": "2026-04-20T14:30:00Z",
        "participants_count": 1
    }
    """

    def post(self, request):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Get user details (simplified: would fetch from DB)
            username = f"user_{user_id}"
            avatar = None

            # Parse request
            body = _json(request)
            _bget = body.get

            try:
                req = CreateChallengeRequest(
                    type_id=_bget("type_id", ""),
                    title=_bget("title", ""),
                    description=_bget("description", ""),
                    visibility=_bget("visibility", "public"),
                    leaderboard_mode=_bget("leaderboard_mode", "mixed"),
                    is_handicapped=_bget("is_handicapped", False),
                    duration_minutes=_bget("duration_minutes", 1440),
                )
            except Exception as e:
                return _json_error("Invalid request.", status=400)

            # Create challenge
            challenge_id, start_time, end_time = ChallengeService.create_challenge(
                creator_id=user_id,
                creator_username=username,
                creator_avatar=avatar,
                request=req,
            )

            return JsonResponse({
                "success": True,
                "challenge_id": challenge_id,
                "title": req.title,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "participants_count": 1,
            })

        except InvalidChallengeTypeError as e:
            return _json_error("Invalid challenge type.", status=400)
        except ChallengeError as e:
            return _json_error("Challenge error.", status=400)
        except Exception as e:
            log.error(f"ChallengeCreateView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Join Challenge ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeJoinView(View):
    """
    POST /api/v1/challenges/join

    Join an existing challenge.

    Request:
    {
        "challenge_id": "ch_jp4k8d2l",
        "handicap_level": 2
    }

    Response:
    {
        "success": true,
        "challenge_id": "ch_jp4k8d2l",
        "joined_at": "2026-04-19T14:30:00Z",
        "participants_count": 25
    }
    """

    def post(self, request):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Get user details
            username = f"user_{user_id}"
            avatar = None

            # Parse request
            body = _json(request)
            _bget = body.get
            challenge_id = _bget("challenge_id", "").strip()
            handicap_level = _bget("handicap_level")

            if not challenge_id:
                return _json_error("Missing challenge_id", status=400)

            # Join challenge
            ChallengeService.join_challenge(
                challenge_id=challenge_id,
                user_id=user_id,
                username=username,
                avatar=avatar,
                handicap_level=handicap_level,
            )

            # Get updated challenge for response
            challenges_col = ChallengeService._get_db()["social_challenges"]
            challenge = challenges_col.find_one({"challenge_id": challenge_id},
                                                {"_id": 0, "participants": 1})
            participants_count = len(challenge.get("participants", [])) if challenge else 0

            return JsonResponse({
                "success": True,
                "challenge_id": challenge_id,
                "joined_at": datetime.utcnow().isoformat(),
                "participants_count": participants_count,
            })

        except ChallengeNotFoundError as e:
            return _json_error("Challenge not found.", status=404)
        except UserAlreadyJoinedError as e:
            return _json_error("Already joined.", status=400)
        except ChallengeError as e:
            return _json_error("Challenge error.", status=400)
        except Exception as e:
            log.error(f"ChallengeJoinView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Update Score (Live Leaderboard) ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeUpdateScoreView(View):
    """
    POST /api/v1/challenges/update-score

    Update user's score in a challenge (live scoring).

    Request:
    {
        "challenge_id": "ch_jp4k8d2l",
        "score_delta": 10,
        "metadata": {"meal_id": "jp_breakfast_001"}
    }

    Response:
    {
        "success": true,
        "challenge_id": "ch_jp4k8d2l",
        "new_score": 42,
        "current_rank": 3
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
            _bget = body.get
            challenge_id = _bget("challenge_id", "").strip()
            score_delta = _bget("score_delta", 0)
            metadata = _bget("metadata", {})

            if not challenge_id:
                return _json_error("Missing challenge_id", status=400)

            if not isinstance(score_delta, int) or score_delta == 0:
                return _json_error("score_delta must be a non-zero integer", status=400)
            if not (-10000 <= score_delta <= 10000):
                return _json_error("score_delta out of range [-10000, 10000]", status=400)

            # Update score
            new_score, current_rank = ChallengeService.update_score(
                challenge_id=challenge_id,
                user_id=user_id,
                score_delta=score_delta,
                metadata=metadata,
            )

            return JsonResponse({
                "success": True,
                "challenge_id": challenge_id,
                "new_score": new_score,
                "current_rank": current_rank,
            })

        except ChallengeNotFoundError as e:
            return _json_error("Challenge not found.", status=404)
        except ChallengeError as e:
            return _json_error("Challenge error.", status=400)
        except Exception as e:
            log.error(f"ChallengeUpdateScoreView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Challenge Leaderboard ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeLeaderboardView(View):
    """
    GET /api/v1/challenges/leaderboard?challenge_id=ch_jp4k8d2l&limit=50

    Get leaderboard for a specific challenge.

    Query Parameters:
    - challenge_id: Required. Challenge ID
    - limit: Optional. Max results (default 100, max 1000)

    Response:
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
            ...
        ]
    }
    """

    def get(self, request):
        try:
            # Get challenge_id from query params
            _qget = request.GET.get
            challenge_id = _qget("challenge_id", "").strip()
            if not challenge_id:
                return _json_error("Missing challenge_id query parameter", status=400)

            # Get optional user_id and limit
            user_id = _require_auth(request)
            try:
                limit = int(_qget("limit", 100))
                limit = min(max(limit, 1), 1000)
            except ValueError:
                limit = 100

            # Get leaderboard
            entries = ChallengeService.get_leaderboard(
                challenge_id=challenge_id,
                user_id=user_id,
                limit=limit,
            )

            # Serialize entries
            entries_data = [
                {
                    "rank": entry.rank,
                    "user_id": entry.user_id,
                    "username": entry.username,
                    "avatar": entry.avatar,
                    "score": entry.score,
                    "handicap_level": entry.handicap_level,
                }
                for entry in entries
            ]

            return JsonResponse({
                "challenge_id": challenge_id,
                "entries": entries_data,
            })

        except ChallengeNotFoundError as e:
            return _json_error("Challenge not found.", status=404)
        except ChallengeError as e:
            return _json_error("Challenge error.", status=400)
        except Exception as e:
            log.error(f"ChallengeLeaderboardView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Cancel Challenge ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeCancelView(View):
    """
    POST /api/v1/challenges/cancel

    Exit/cancel a challenge (applies penalty).

    Request:
    {
        "challenge_id": "ch_jp4k8d2l",
        "reason": "No longer interested"
    }

    Response:
    {
        "success": true,
        "challenge_id": "ch_jp4k8d2l",
        "penalty_coins": 2
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
            _bget = body.get
            challenge_id = _bget("challenge_id", "").strip()
            reason = _bget("reason")

            if not challenge_id:
                return _json_error("Missing challenge_id", status=400)

            # Cancel challenge
            penalty = ChallengeService.cancel_challenge(
                challenge_id=challenge_id,
                user_id=user_id,
                reason=reason,
            )

            return JsonResponse({
                "success": True,
                "challenge_id": challenge_id,
                "penalty_coins": penalty,
            })

        except ChallengeNotFoundError as e:
            return _json_error("Challenge not found.", status=404)
        except ChallengeError as e:
            return _json_error("Challenge error.", status=400)
        except Exception as e:
            log.error(f"ChallengeCancelView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── User's Active Challenges ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class ChallengeActiveView(View):
    """
    GET /api/v1/challenges/active?limit=50

    Get user's active and upcoming challenges.

    Query Parameters:
    - limit: Optional. Max results (default 50, max 500)

    Response:
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
                limit = min(max(limit, 1), 500)
            except ValueError:
                limit = 50

            # Get active challenges
            docs, total = ChallengeService.get_active_challenges(
                user_id=user_id,
                limit=limit,
            )

            # Format response
            challenges_data = []
            for doc in docs:
                # Find user's participation data
                all_participants = doc.get("participants", [])
                user_part = next(
                    (p for p in all_participants if p["user_id"] == user_id),
                    None
                )

                # Calculate rank
                participants = [p for p in all_participants if p["is_active"]]
                sorted_parts = sorted(
                    participants,
                    key=lambda p: (-p["score"], all_participants.index(p))
                )
                user_rank = next(
                    (i + 1 for i, p in enumerate(sorted_parts) if p["user_id"] == user_id),
                    len(sorted_parts)
                )

                challenges_data.append({
                    "challenge_id": doc["challenge_id"],
                    "type_id": doc["type_id"],
                    "title": doc["title"],
                    "status": doc["status"],
                    "participants_count": len(participants),
                    "user_rank": user_rank,
                    "user_score": user_part["score"] if user_part else 0,
                    "end_time": doc["end_time"],
                })

            return JsonResponse({
                "total": total,
                "challenges": challenges_data,
            })

        except Exception as e:
            log.error(f"ChallengeActiveView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
