"""
admin_api/views/discovery_game_views.py
======================================
Discovery games API endpoints: types, sessions, gameplay, results.

Endpoints:
  GET  /api/v1/discovery-games/types - List available games
  POST /api/v1/discovery-games/start - Start new game
  POST /api/v1/discovery-games/answer - Submit answer
  GET  /api/v1/discovery-games/session/:session_id - Get session
  POST /api/v1/discovery-games/abandon - Abandon game
"""

import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_auth
from gamification.models.discovery_game import DISCOVERY_GAME_TYPES
from gamification.services.discovery_game_service import (
    DiscoveryGameService, DiscoveryGameError, SessionNotFoundError,
    GameTypeNotFoundError
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
# ── Game Types ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryGameTypesView(View):
    """
    GET /api/v1/discovery-games/types

    Get all available discovery game types.

    Response:
    {
        "count": 5,
        "games": [
            {
                "game_type_id": "trait_discovery",
                "name_en": "Trait Discovery",
                "name_tr": "Sıfat Keşfi",
                "description_en": "Discover which personality traits match you",
                "game_mode": "trait_discovery",
                "coin_reward_win": 30,
                "coin_reward_play": 10
            },
            ...
        ]
    }
    """

    def get(self, request):
        try:
            games_data = [
                {
                    "game_type_id": g.game_type_id,
                    "name_en": g.name_en,
                    "name_tr": g.name_tr,
                    "description_en": g.description_en,
                    "description_tr": g.description_tr,
                    "game_mode": g.game_mode,
                    "duration_seconds": g.duration_seconds,
                    "coin_reward_win": g.coin_reward_win,
                    "coin_reward_play": g.coin_reward_play,
                    "learning_focus": g.learning_focus,
                }
                for g in DISCOVERY_GAME_TYPES.values()
            ]

            return JsonResponse({
                "count": len(games_data),
                "games": games_data,
            })

        except Exception as e:
            log.error(f"DiscoveryGameTypesView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Start Game ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryGameStartView(View):
    """
    POST /api/v1/discovery-games/start

    Start a new discovery game session.

    Request:
    {
        "game_type": "trait_discovery",
        "difficulty": "normal",
        "language": "en"
    }

    Response:
    {
        "session_id": "dg_xyz123",
        "game_type": "trait_discovery",
        "question": {
            "question_id": "td_001",
            "question_number": 1,
            "total_questions": 5,
            "question_text": "When facing a problem...",
            "question_type": "multi_choice",
            "options": ["Think logically", "Trust gut", "Ask others"]
        }
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
            game_type = _bget("game_type", "").strip()
            difficulty = _bget("difficulty", "normal")
            language = _bget("language", "en")

            if not game_type:
                return _json_error("Missing game_type", status=400)

            # Start game
            session_id, first_question = DiscoveryGameService.start_game(
                user_id=user_id,
                game_type=game_type,
                difficulty=difficulty,
                language=language,
            )

            return JsonResponse({
                "session_id": session_id,
                "game_type": game_type,
                "question": first_question,
            })

        except GameTypeNotFoundError as e:
            return _json_error("Game type not found.", status=404)
        except DiscoveryGameError as e:
            return _json_error("Game error.", status=400)
        except Exception as e:
            log.error(f"DiscoveryGameStartView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Submit Answer ──────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryGameAnswerView(View):
    """
    POST /api/v1/discovery-games/answer

    Submit answer to a discovery game question.

    Request:
    {
        "session_id": "dg_xyz123",
        "question_id": "td_001",
        "answer": 0  # Index, value, or string
    }

    Response (if game continues):
    {
        "is_correct": true,
        "coins_earned": 0,  # Only on completion
        "next_question": {
            "question_id": "td_002",
            "question_number": 2,
            "total_questions": 5,
            ...
        }
    }

    Response (if game completes):
    {
        "is_correct": true,
        "game_complete": true,
        "accuracy_percent": 80.0,
        "coins_earned": 30,
        "xp_earned": 10,
        "traits_discovered": ["dürüst", "analitik"],
        "insights": "Excellent! You have strong trait awareness."
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
            session_id = _bget("session_id", "").strip()
            question_id = _bget("question_id", "").strip()
            answer = _bget("answer")

            if not session_id or not question_id or answer is None:
                return _json_error("Missing session_id, question_id, or answer", status=400)

            # Submit answer
            is_correct, result = DiscoveryGameService.submit_answer(
                session_id=session_id,
                user_id=user_id,
                question_id=question_id,
                answer=answer,
            )

            # Check if game complete
            if isinstance(result, dict) and "insights" in result:
                # Game complete
                _resget = result.get
                return JsonResponse({
                    "is_correct": is_correct,
                    "game_complete": True,
                    "accuracy_percent": _resget("accuracy_percent"),
                    "coins_earned": _resget("coins_earned"),
                    "xp_earned": _resget("xp_earned"),
                    "traits_discovered": _resget("traits_discovered"),
                    "insights": _resget("insights"),
                })
            else:
                # Next question
                return JsonResponse({
                    "is_correct": is_correct,
                    "game_complete": False,
                    "next_question": result,
                })

        except SessionNotFoundError as e:
            return _json_error("Session not found.", status=404)
        except DiscoveryGameError as e:
            return _json_error("Game error.", status=400)
        except Exception as e:
            log.error(f"DiscoveryGameAnswerView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Session Details ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryGameSessionView(View):
    """
    GET /api/v1/discovery-games/session/:session_id

    Get details of a discovery game session.

    Response:
    {
        "session_id": "dg_xyz123",
        "user_id": 123,
        "game_type": "trait_discovery",
        "status": "active",
        "questions_answered": 2,
        "accuracy_percent": 75.0,
        "coins_earned": 0,
        "traits_discovered": ["dürüst"],
        "started_at": "2026-04-19T10:00:00Z"
    }
    """

    def get(self, request, session_id):
        try:
            # Authenticate user
            user_id = _require_auth(request)
            if not user_id:
                return _json_error("Unauthorized", status=401)

            # Get session
            session = DiscoveryGameService.get_session(
                session_id=session_id,
                user_id=user_id,
            )

            return JsonResponse({
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "game_type": session["game_type"],
                "status": session["status"],
                "questions_answered": session["questions_answered"],
                "accuracy_percent": session["accuracy_percent"],
                "coins_earned": session["coins_earned"],
                "xp_earned": session["xp_earned"],
                "traits_discovered": session["traits_discovered"],
                "started_at": session["started_at"],
                "completed_at": session.get("completed_at"),
            })

        except SessionNotFoundError as e:
            return _json_error("Session not found.", status=404)
        except DiscoveryGameError as e:
            return _json_error("Game error.", status=400)
        except Exception as e:
            log.error(f"DiscoveryGameSessionView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Abandon Game ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DiscoveryGameAbandonView(View):
    """
    POST /api/v1/discovery-games/abandon

    Abandon a game session in progress.

    Request:
    {
        "session_id": "dg_xyz123"
    }

    Response:
    {
        "success": true,
        "session_id": "dg_xyz123",
        "message": "Game abandoned"
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
            session_id = body.get("session_id", "").strip()

            if not session_id:
                return _json_error("Missing session_id", status=400)

            # Abandon game
            DiscoveryGameService.abandon_game(
                session_id=session_id,
                user_id=user_id,
            )

            return JsonResponse({
                "success": True,
                "session_id": session_id,
                "message": "Game abandoned",
            })

        except SessionNotFoundError as e:
            return _json_error("Session not found.", status=404)
        except DiscoveryGameError as e:
            return _json_error("Game error.", status=400)
        except Exception as e:
            log.error(f"DiscoveryGameAbandonView error: {e}", exc_info=True)
            return _json_error("Internal server error", status=500)
