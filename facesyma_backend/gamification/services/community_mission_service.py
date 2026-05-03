"""Community mission service — MongoDB-backed community missions."""
import random
import string
from datetime import datetime, timedelta
from typing import Tuple
from gamification.models.community_mission import MISSION_TYPES


class MissionError(Exception):
    pass


class MissionNotFoundError(MissionError):
    pass


class MissionTypeNotFoundError(MissionError):
    pass


class UserAlreadyJoinedError(MissionError):
    pass


def _gen_id():
    return "miss_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class CommunityMissionService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def get_active_missions(community_id=None, limit: int = 10) -> list:
        db = CommunityMissionService._db()
        now_iso = datetime.utcnow().isoformat()
        match = {"status": "active", "end_time": {"$gte": now_iso}}
        if community_id:
            match["community_id"] = community_id
        docs = list(
            db["community_missions"]
            .find(match, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        return docs

    @staticmethod
    def join_mission(
        user_id: int,
        mission_id: str,
        username: str,
        avatar=None,
    ) -> dict:
        db = CommunityMissionService._db()
        col = db["community_missions"]
        mission = col.find_one({"mission_id": mission_id})
        if not mission:
            raise MissionNotFoundError(mission_id)
        participants = mission.get("participants", [])
        if any(p["user_id"] == user_id for p in participants):
            raise UserAlreadyJoinedError(user_id)
        col.update_one(
            {"mission_id": mission_id},
            {"$push": {"participants": {
                "user_id": user_id,
                "username": username,
                "avatar": avatar,
                "contributed": 0,
                "joined_at": datetime.utcnow().isoformat(),
            }}},
        )
        updated = col.find_one({"mission_id": mission_id}, {"_id": 0})
        return updated or {}

    @staticmethod
    def contribute_to_mission(
        user_id: int,
        mission_id: str,
        amount: int,
        metadata=None,
    ):
        db = CommunityMissionService._db()
        col = db["community_missions"]
        mission = col.find_one({"mission_id": mission_id})
        if not mission:
            raise MissionNotFoundError(mission_id)
        if not any(p["user_id"] == user_id for p in mission.get("participants", [])):
            raise MissionError("User not a participant")
        col.update_one(
            {"mission_id": mission_id, "participants.user_id": user_id},
            {"$inc": {
                "participants.$.contributed": amount,
                "total_contributed": amount,
            }},
        )
        updated = col.find_one({"mission_id": mission_id})
        total = int(updated.get("total_contributed", 0))
        target = int(updated.get("target_value", 1))
        is_complete = total >= target
        if is_complete and updated.get("status") == "active":
            col.update_one(
                {"mission_id": mission_id},
                {"$set": {"status": "completed", "completed_at": datetime.utcnow().isoformat()}},
            )
        mtype = MISSION_TYPES.get(updated.get("mission_type_id", ""))
        coins_earned = mtype.coin_reward_per_person if (is_complete and mtype) else 0
        return total, is_complete, coins_earned

    @staticmethod
    def contribute(
        mission_id: str,
        user_id: int,
        contribution: int,
        metadata=None,
    ) -> Tuple[int, float]:
        """View-facing method. Returns (new_progress, progress_percent)."""
        total, is_complete, _ = CommunityMissionService.contribute_to_mission(
            user_id=user_id,
            mission_id=mission_id,
            amount=contribution,
            metadata=metadata,
        )
        db = CommunityMissionService._db()
        mission = db["community_missions"].find_one(
            {"mission_id": mission_id}, {"target_value": 1}
        )
        target = int(mission.get("target_value", 1)) if mission else 1
        progress_percent = min(100.0, round(total / target * 100, 2)) if target else 0.0
        return total, progress_percent

    @staticmethod
    def get_mission(mission_id: str) -> dict:
        db = CommunityMissionService._db()
        mission = db["community_missions"].find_one({"mission_id": mission_id}, {"_id": 0})
        if not mission:
            raise MissionNotFoundError(mission_id)
        return mission

    @staticmethod
    def get_mission_leaderboard(mission_id: str, limit: int = 100) -> list:
        db = CommunityMissionService._db()
        mission = db["community_missions"].find_one(
            {"mission_id": mission_id}, {"participants": 1}
        )
        if not mission:
            raise MissionNotFoundError(mission_id)
        sorted_p = sorted(
            mission.get("participants", []),
            key=lambda p: p.get("contributed", 0),
            reverse=True,
        )[:limit]
        return [
            {
                "rank": i + 1,
                "user_id": p["user_id"],
                "username": p.get("username", f"user_{p['user_id']}"),
                "avatar": p.get("avatar"),
                "contributed": p.get("contributed", 0),
            }
            for i, p in enumerate(sorted_p)
        ]
