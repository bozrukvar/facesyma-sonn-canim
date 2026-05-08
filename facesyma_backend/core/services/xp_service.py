"""XP & Level service — MongoDB-backed XP and level management."""
import math
import random
import string
from datetime import datetime
from typing import Optional, Tuple, List


# ── Level formula ─────────────────────────────────────────────────────────────
# level = floor(sqrt(xp / 100)) + 1   (level 1 starts at 0 XP)
# XP needed to reach level L = (L-1)^2 * 100
# XP needed for level L → L+1 = (2L - 1) * 100

MAX_LEVEL = 50


def xp_to_level(xp: int) -> int:
    return min(MAX_LEVEL, int(math.floor(math.sqrt(max(0, xp) / 100))) + 1)


def level_start_xp(level: int) -> int:
    """Total XP needed to reach this level."""
    return (level - 1) ** 2 * 100


def level_end_xp(level: int) -> int:
    """Total XP needed to reach next level."""
    return level ** 2 * 100


def level_progress(xp: int) -> dict:
    """Returns full level info for a given XP amount."""
    level    = xp_to_level(xp)
    start    = level_start_xp(level)
    end      = level_end_xp(level)
    span     = end - start
    progress = round((xp - start) / span * 100) if span > 0 else 100
    return {
        "level":          level,
        "xp":             xp,
        "xp_to_next":     max(0, end - xp),
        "level_progress": min(100, progress),   # percent 0-100
        "level_start_xp": start,
        "level_end_xp":   end,
    }


# ── XP amounts ────────────────────────────────────────────────────────────────
class XPReward:
    DAILY_QUEST      = 50
    WORDLE_WIN_FIRST = 75
    WORDLE_WIN_BASE  = 30   # + (5 * attempts_left) on top
    SPEED_MATCH_BASE = 10   # + correct_count * 4
    POLL_CORRECT     = 15
    POLL_VOTE        = 5
    MEMORY_BASE      = 20   # + moves bonus
    SPIN_BASE        = 1    # multiplied by segment value
    MEAL_CORRECT     = 50
    MEAL_WRONG       = 10
    BADGE_BRONZE     = 100
    BADGE_SILVER     = 250
    BADGE_GOLD       = 500
    BADGE_PLATINUM   = 1000
    CHALLENGE_WIN    = 150
    MISSION_CONTRIB  = 25


# ── XP Service ────────────────────────────────────────────────────────────────
class XPError(Exception):
    pass


class XPService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def get_xp(user_id: int) -> int:
        user = XPService._db()["appfaceapi_myuser"].find_one(
            {"id": user_id}, {"xp": 1, "_id": 0}
        )
        if not user:
            raise XPError(f"User {user_id} not found")
        return int(user.get("xp", 0))

    @staticmethod
    def get_stats(user_id: int) -> dict:
        user = XPService._db()["appfaceapi_myuser"].find_one(
            {"id": user_id},
            {"xp": 1, "streak_count": 1, "last_daily_quest": 1, "_id": 0},
        )
        if not user:
            raise XPError(f"User {user_id} not found")
        xp = int(user.get("xp", 0))
        return {
            **level_progress(xp),
            "streak_days":       int(user.get("streak_count", 0)),
            "last_daily_quest":  user.get("last_daily_quest"),
        }

    @staticmethod
    def add_xp(user_id: int, amount: int, reason: str) -> dict:
        """Add XP and return updated level info."""
        if amount <= 0:
            raise XPError("Amount must be positive")
        db = XPService._db()
        result = db["appfaceapi_myuser"].find_one_and_update(
            {"id": user_id},
            {"$inc": {"xp": amount},
             "$setOnInsert": {"streak_count": 0}},
            return_document=True,
            projection={"xp": 1, "_id": 0},
            upsert=False,
        )
        if not result:
            raise XPError(f"User {user_id} not found")
        new_xp = int(result.get("xp", 0))
        tx_id = "xp_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        db["xp_transactions"].insert_one({
            "transaction_id": tx_id,
            "user_id":        user_id,
            "amount":         amount,
            "reason":         reason,
            "xp_after":       new_xp,
            "created_at":     datetime.utcnow().isoformat(),
        })
        return level_progress(new_xp)

    @staticmethod
    def get_transaction_history(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        col = XPService._db()["xp_transactions"]
        query = {"user_id": user_id}
        total = col.count_documents(query)
        docs  = list(
            col.find(query, {"_id": 0})
               .sort("created_at", -1)
               .skip(offset)
               .limit(limit)
        )
        return docs, total

    @staticmethod
    def update_daily_quest_streak(user_id: int) -> int:
        db   = XPService._db()
        user = db["appfaceapi_myuser"].find_one(
            {"id": user_id}, {"last_daily_quest": 1, "streak_count": 1, "_id": 0}
        )
        if not user:
            raise XPError(f"User {user_id} not found")
        now      = datetime.utcnow()
        last_str = user.get("last_daily_quest")
        streak   = int(user.get("streak_count", 0))
        if last_str:
            try:
                last_dt = datetime.fromisoformat(last_str)
                diff    = (now.date() - last_dt.date()).days
                if diff == 0:
                    return streak
                streak = streak + 1 if diff == 1 else 1
            except Exception:
                streak = 1
        else:
            streak = 1
        db["appfaceapi_myuser"].update_one(
            {"id": user_id},
            {"$set": {"streak_count": streak, "last_daily_quest": now.isoformat()}},
        )
        return streak

    @staticmethod
    def admin_adjust_xp(user_id: int, amount: int, reason: str, admin_id) -> dict:
        if amount == 0:
            xp = XPService.get_xp(user_id)
            return level_progress(xp)
        return XPService.add_xp(user_id, abs(amount), f"admin_adjust: {reason}")
