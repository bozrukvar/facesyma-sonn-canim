"""
admin_api/views/coin_views.py
============================
Coin system API endpoints: balance, transactions, admin operations.

Endpoints:
  GET  /api/v1/coins/balance - Get user balance
  GET  /api/v1/coins/stats - Get coin statistics
  GET  /api/v1/coins/history - Get transaction history
  POST /api/v1/coins/add - Add coins (internal use, e.g., quest completion)
  POST /api/v1/coins/deduct - Deduct coins (spending, stakes)
  POST /api/v1/coins/admin/adjust - Admin manual adjustment
  POST /api/v1/coins/daily-quest - Complete daily quest & claim reward
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from admin_api.utils.auth import _require_admin, _require_auth
from core.models.transaction import TransactionType
from core.services.coin_service import (
    CoinService, CoinError, InsufficientCoinsError, InvalidAmountError
)

log = logging.getLogger(__name__)

_STREAK_MILESTONES = frozenset({7, 14, 30, 100, 365})
_STREAK_BONUS_MULTIPLIERS = {7: 1.3, 14: 1.6, 30: 2.0, 100: 2.5, 365: 5.0}


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
# ── Coin Balance & Stats ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoinBalanceView(View):
    """
    GET /api/v1/coins/balance

    Get user's current coin balance.

    Response:
      {
        "user_id": 1,
        "balance": 150,
        "currency": "coins"
      }
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 401)

        try:
            balance = CoinService.get_balance(user_id)
            return JsonResponse({
                "user_id": user_id,
                "balance": balance,
                "currency": "coins",
            })
        except CoinError as e:
            return _json_error(str(e), 404)


@method_decorator(csrf_exempt, name='dispatch')
class CoinStatsView(View):
    """
    GET /api/v1/coins/stats

    Get user's coin statistics (earned, spent, balance, streak).

    Response:
      {
        "user_id": 1,
        "current_balance": 150,
        "total_earned": 500,
        "total_spent": 350,
        "streak_days": 7,
        "last_daily_quest": "2026-04-19T14:30:00"
      }
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 401)

        try:
            stats = CoinService.get_stats(user_id)
            return JsonResponse({
                "user_id": user_id,
                **stats,
            })
        except CoinError as e:
            return _json_error(str(e), 404)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Transaction History ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoinHistoryView(View):
    """
    GET /api/v1/coins/history

    Get user's transaction history (paginated, filterable).

    Query params:
      - limit: int (default 50, max 200)
      - offset: int (default 0)
      - type: str (optional, filter by TransactionType)

    Example:
      GET /api/v1/coins/history?limit=20&offset=0&type=coaching_quest

    Response:
      {
        "user_id": 1,
        "transactions": [
          {
            "id": "ObjectId",
            "amount": 10,
            "type": "coaching_quest",
            "description": "Daily coaching quest completed",
            "balance_after": 160,
            "created_at": "2026-04-19T14:30:00"
          },
          ...
        ],
        "total": 42,
        "limit": 20,
        "offset": 0
      }
    """

    def get(self, request):
        try:
            user_id = _require_auth(request)
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 401)

        _qget = request.GET.get
        try:
            limit = min(max(1, int(_qget("limit", 50))), 200)
            offset = max(int(_qget("offset", 0)), 0)
        except (ValueError, TypeError):
            limit, offset = 50, 0
        trans_type = _qget("type", None)

        try:
            transactions, total = CoinService.get_transaction_history(
                user_id=user_id,
                limit=limit,
                offset=offset,
                transaction_type=trans_type,
            )
            return JsonResponse({
                "user_id": user_id,
                "transactions": transactions,
                "total": total,
                "limit": limit,
                "offset": offset,
            })
        except CoinError as e:
            return _json_error(str(e), 404)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Coin Operations (Internal) ─────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoinAddView(View):
    """
    POST /api/v1/coins/add

    Add coins to user (internal: coaching quests, challenges, etc).

    IMPORTANT: This endpoint requires ADMIN auth (internal use only).
    External APIs should call indirectly through game endpoints.

    Request body:
      {
        "user_id": 1,
        "amount": 10,
        "type": "coaching_quest",
        "description": "Daily coaching quest completed",
        "metadata": {
          "module": "diet",
          "day": 1
        }
      }

    Response:
      {
        "user_id": 1,
        "new_balance": 160,
        "transaction_id": "ObjectId",
        "amount": 10
      }
    """

    def post(self, request):
        try:
            _require_admin(request)  # Internal use only
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 403)

        body = _json(request)
        _bget = body.get
        user_id = _bget("user_id")
        amount = _bget("amount")
        trans_type = _bget("type", "unknown")
        description = _bget("description", "")
        metadata = _bget("metadata")

        if not user_id or amount is None:
            return _json_error("Missing user_id or amount", 400)

        try:
            trans_type = TransactionType(trans_type)
        except ValueError:
            return _json_error(f"Invalid transaction type: {trans_type}", 400)

        try:
            new_balance, trans_id = CoinService.add_coins(
                user_id=user_id,
                amount=amount,
                transaction_type=trans_type,
                description=description,
                metadata=metadata,
            )
            return JsonResponse({
                "user_id": user_id,
                "new_balance": new_balance,
                "transaction_id": trans_id,
                "amount": amount,
            })
        except (InvalidAmountError, CoinError) as e:
            return _json_error(str(e), 400)


@method_decorator(csrf_exempt, name='dispatch')
class CoinDeductView(View):
    """
    POST /api/v1/coins/deduct

    Deduct coins from user (spending, challenge stakes, etc).

    IMPORTANT: This endpoint requires ADMIN auth (internal use only).

    Request body:
      {
        "user_id": 1,
        "amount": 10,
        "type": "challenge_entry",
        "description": "Social challenge stake",
        "metadata": {
          "challenge_id": "abc123"
        },
        "allow_negative": false
      }

    Response:
      {
        "user_id": 1,
        "new_balance": 140,
        "transaction_id": "ObjectId",
        "amount": 10
      }
    """

    def post(self, request):
        try:
            _require_admin(request)  # Internal use only
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 403)

        body = _json(request)
        _bget = body.get
        user_id = _bget("user_id")
        amount = _bget("amount")
        trans_type = _bget("type", "unknown")
        description = _bget("description", "")
        metadata = _bget("metadata")
        allow_negative = _bget("allow_negative", False)

        if not user_id or amount is None:
            return _json_error("Missing user_id or amount", 400)

        try:
            trans_type = TransactionType(trans_type)
        except ValueError:
            return _json_error(f"Invalid transaction type: {trans_type}", 400)

        try:
            new_balance, trans_id = CoinService.deduct_coins(
                user_id=user_id,
                amount=amount,
                transaction_type=trans_type,
                description=description,
                metadata=metadata,
                allow_negative=allow_negative,
            )
            return JsonResponse({
                "user_id": user_id,
                "new_balance": new_balance,
                "transaction_id": trans_id,
                "amount": amount,
            })
        except InsufficientCoinsError:
            return _json_error("Insufficient coins", 402)
        except (InvalidAmountError, CoinError) as e:
            return _json_error(str(e), 400)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Daily Quest (Main Game Loop) ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class DailyQuestCompleteView(View):
    """
    POST /api/v1/coins/daily-quest/complete

    Complete daily coaching quest and claim reward.

    This is the main entry point for Coaching Quests:
    - Updates streak
    - Awards coins (+10-40 depending on modules completed)
    - Logs transaction

    Request body:
      {
        "modules_completed": 2,  # 1-4
        "bonus_points": 0  # optional: additional reward
      }

    Response:
      {
        "user_id": 1,
        "coins_earned": 40,
        "new_balance": 190,
        "streak_days": 7,
        "streak_bonus": true,
        "transaction_id": "ObjectId"
      }
    """

    def post(self, request):
        try:
            user_id = _require_auth(request)
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 401)

        body = _json(request)
        _bget = body.get
        modules_completed = _bget("modules_completed", 1)
        bonus_points = _bget("bonus_points", 0)

        if not 1 <= modules_completed <= 4:
            return _json_error("modules_completed must be 1-4", 400)

        try:
            bonus_points = int(bonus_points)
        except (ValueError, TypeError):
            bonus_points = 0
        if not 0 <= bonus_points <= 100:
            return _json_error("bonus_points must be between 0 and 100", 400)

        try:
            # Calculate coins earned
            base_coins = modules_completed * 10
            total_coins = min(base_coins + bonus_points, 10000)

            _cas = CoinService.add_coins
            _tcq = TransactionType.COACHING_QUEST
            # Update streak and award coins
            new_streak = CoinService.update_daily_quest_streak(user_id)
            new_balance, trans_id = _cas(
                user_id=user_id,
                amount=total_coins,
                transaction_type=_tcq,
                description=f"Daily coaching quest ({modules_completed} modules)",
                metadata={
                    "modules": modules_completed,
                    "bonus": bonus_points,
                    "streak": new_streak,
                },
            )

            # Check if streak milestone reached for bonus
            streak_bonus = new_streak in _STREAK_MILESTONES
            if streak_bonus:
                bonus_multiplier = _STREAK_BONUS_MULTIPLIERS.get(new_streak, 1.0)
                bonus_amount = int(total_coins * (bonus_multiplier - 1))
                new_balance, _ = _cas(
                    user_id=user_id,
                    amount=bonus_amount,
                    transaction_type=_tcq,
                    description=f"Streak bonus: {new_streak} days",
                    metadata={"streak_milestone": new_streak},
                )

            return JsonResponse({
                "user_id": user_id,
                "coins_earned": total_coins,
                "new_balance": new_balance,
                "streak_days": new_streak,
                "streak_bonus": streak_bonus,
                "transaction_id": trans_id,
            })

        except CoinError as e:
            return _json_error(str(e), 400)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Admin Operations ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@method_decorator(csrf_exempt, name='dispatch')
class CoinAdminAdjustView(View):
    """
    POST /api/v1/coins/admin/adjust

    Admin manual coin adjustment (for support, testing, corrections).

    REQUIRES: Admin authentication

    Request body:
      {
        "user_id": 1,
        "amount": 50,
        "reason": "Support refund - double charge"
      }

    Response:
      {
        "user_id": 1,
        "new_balance": 200,
        "adjustment": 50,
        "transaction_id": "ObjectId"
      }
    """

    def post(self, request):
        try:
            admin_id = _require_admin(request)
        except (ValueError, PermissionError) as e:
            return _json_error(str(e), 403)

        body = _json(request)
        _bget = body.get
        user_id = _bget("user_id")
        amount = _bget("amount")
        reason = _bget("reason", "Manual adjustment")

        if not user_id or amount is None:
            return _json_error("Missing user_id or amount", 400)

        try:
            new_balance, trans_id = CoinService.admin_adjust_coins(
                user_id=user_id,
                amount=amount,
                reason=reason,
                admin_id=admin_id,
            )
            return JsonResponse({
                "user_id": user_id,
                "new_balance": new_balance,
                "adjustment": amount,
                "transaction_id": trans_id,
            })
        except CoinError as e:
            return _json_error(str(e), 400)
