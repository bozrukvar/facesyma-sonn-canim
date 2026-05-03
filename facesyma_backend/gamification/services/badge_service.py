"""Badge service — MongoDB-backed badge management."""
from datetime import datetime
from types import SimpleNamespace
from gamification.models.badge import BADGE_DEFINITIONS


class BadgeError(Exception):
    pass


class BadgeNotFoundError(BadgeError):
    pass


class BadgeService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def list_all_badges():
        return list(BADGE_DEFINITIONS.values())

    @staticmethod
    def get_badge_definition(badge_id: str):
        defn = BADGE_DEFINITIONS.get(badge_id)
        if not defn:
            raise BadgeNotFoundError(f"Badge {badge_id} not found")
        return defn

    @staticmethod
    def get_user_badges(user_id: int) -> dict:
        col = BadgeService._db()["user_badges"]
        docs = list(col.find({"user_id": user_id}, {"_id": 0}))
        result = {}
        for doc in docs:
            bid = doc.get("badge_id")
            if bid:
                result[bid] = {
                    "badge_id": bid,
                    "current_tier": doc.get("current_tier", "bronze"),
                    "current_progress": doc.get("current_progress", 0),
                    "unlocked_at": doc.get("unlocked_at"),
                    "tier_unlocks": doc.get("tier_unlocks", {}),
                    "total_coins_earned": doc.get("total_coins_earned", 0),
                }
        return result

    @staticmethod
    def award_badge(user_id: int, badge_id: str, progress: int = 1) -> dict:
        if badge_id not in BADGE_DEFINITIONS:
            raise BadgeNotFoundError(f"Badge {badge_id} not found")
        defn = BADGE_DEFINITIONS[badge_id]
        col = BadgeService._db()["user_badges"]
        now_iso = datetime.utcnow().isoformat()
        existing = col.find_one({"user_id": user_id, "badge_id": badge_id}, {"_id": 0})
        current_progress = (existing.get("current_progress", 0) if existing else 0) + progress
        tier_unlocks = existing.get("tier_unlocks", {}) if existing else {}
        current_tier = existing.get("current_tier") if existing else None
        coins_earned = existing.get("total_coins_earned", 0) if existing else 0

        for tier_obj in defn.tiers:
            if current_progress >= tier_obj.threshold:
                if tier_obj.tier not in tier_unlocks:
                    tier_unlocks[tier_obj.tier] = now_iso
                    coins_earned += defn.coin_reward_per_tier
                current_tier = tier_obj.tier

        col.update_one(
            {"user_id": user_id, "badge_id": badge_id},
            {"$set": {
                "user_id": user_id,
                "badge_id": badge_id,
                "current_tier": current_tier or "bronze",
                "current_progress": current_progress,
                "unlocked_at": existing.get("unlocked_at", now_iso) if existing else now_iso,
                "tier_unlocks": tier_unlocks,
                "total_coins_earned": coins_earned,
                "updated_at": now_iso,
            }},
            upsert=True,
        )
        return {"badge_id": badge_id, "current_tier": current_tier, "progress": current_progress}

    @staticmethod
    def get_badge_leaderboard(
        badge_id: str,
        metric: str = "platinum_count",
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        if badge_id not in BADGE_DEFINITIONS:
            raise BadgeNotFoundError(f"Badge {badge_id} not found")
        db = BadgeService._db()
        badge_col = db["user_badges"]
        users_col = db["appfaceapi_myuser"]
        _TIER_RANK = {"platinum": 4, "gold": 3, "silver": 2, "bronze": 1}
        sort_field = "current_progress" if metric == "current_progress" else "current_progress"
        pipeline = [
            {"$match": {"badge_id": badge_id}},
            {"$sort": {"current_progress": -1}},
            {"$skip": offset},
            {"$limit": limit},
        ]
        docs = list(badge_col.aggregate(pipeline))
        user_ids = [d["user_id"] for d in docs]
        users_map = {
            u["id"]: u for u in users_col.find(
                {"id": {"$in": user_ids}}, {"id": 1, "username": 1, "avatar": 1, "_id": 0}
            )
        }
        entries = []
        for rank, doc in enumerate(docs, 1):
            uid = doc["user_id"]
            user = users_map.get(uid, {})
            tier = doc.get("current_tier")
            tier_unlocks = doc.get("tier_unlocks", {})
            platinum_count = 1 if tier == "platinum" else 0
            entries.append(SimpleNamespace(
                rank=rank,
                user_id=uid,
                username=user.get("username", f"user_{uid}"),
                avatar=user.get("avatar"),
                current_tier=tier,
                current_progress=doc.get("current_progress", 0),
                platinum_count=platinum_count,
            ))
        return entries
