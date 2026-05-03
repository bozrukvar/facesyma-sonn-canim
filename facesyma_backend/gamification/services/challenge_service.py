"""Challenge service — MongoDB-backed social challenges."""
import random
import string
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Tuple, List, Optional
from gamification.models.challenge import CHALLENGE_TYPES


class ChallengeError(Exception):
    pass


class ChallengeNotFoundError(ChallengeError):
    pass


class InvalidChallengeTypeError(ChallengeError):
    pass


class UserAlreadyJoinedError(ChallengeError):
    pass


def _gen_id():
    return "ch_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def _entry(rank, p):
    return SimpleNamespace(
        rank=rank,
        user_id=p["user_id"],
        username=p.get("username", f"user_{p['user_id']}"),
        avatar=p.get("avatar"),
        score=p.get("score", 0),
        handicap_level=p.get("handicap_level"),
    )


class ChallengeService:

    @staticmethod
    def _get_db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def create_challenge(
        creator_id: int,
        creator_username: str,
        creator_avatar: Optional[str],
        request,
    ) -> Tuple[str, datetime, datetime]:
        if request.type_id not in CHALLENGE_TYPES:
            raise InvalidChallengeTypeError(f"Unknown type: {request.type_id}")
        ctype = CHALLENGE_TYPES[request.type_id]
        now = datetime.utcnow()
        end = now + timedelta(minutes=request.duration_minutes or ctype.duration_minutes)
        challenge_id = _gen_id()
        db = ChallengeService._get_db()
        db["social_challenges"].insert_one({
            "challenge_id": challenge_id,
            "type_id": request.type_id,
            "title": request.title,
            "description": request.description,
            "visibility": request.visibility,
            "leaderboard_mode": request.leaderboard_mode,
            "is_handicapped": request.is_handicapped,
            "duration_minutes": request.duration_minutes,
            "status": "active",
            "creator_id": creator_id,
            "start_time": now.isoformat(),
            "end_time": end.isoformat(),
            "participants": [{
                "user_id": creator_id,
                "username": creator_username,
                "avatar": creator_avatar,
                "score": 0,
                "handicap_level": None,
                "joined_at": now.isoformat(),
                "is_active": True,
            }],
            "created_at": now.isoformat(),
        })
        return challenge_id, now, end

    @staticmethod
    def join_challenge(
        challenge_id: str,
        user_id: int,
        username: str,
        avatar: Optional[str],
        handicap_level: Optional[int],
    ) -> None:
        db = ChallengeService._get_db()
        col = db["social_challenges"]
        challenge = col.find_one({"challenge_id": challenge_id}, {"participants": 1, "status": 1})
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        participants = challenge.get("participants", [])
        if any(p["user_id"] == user_id for p in participants):
            raise UserAlreadyJoinedError(user_id)
        col.update_one(
            {"challenge_id": challenge_id},
            {"$push": {"participants": {
                "user_id": user_id,
                "username": username,
                "avatar": avatar,
                "score": 0,
                "handicap_level": handicap_level,
                "joined_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }}},
        )

    @staticmethod
    def update_score(
        challenge_id: str,
        user_id: int,
        score_delta: int,
        metadata: Optional[dict] = None,
    ) -> Tuple[int, int]:
        db = ChallengeService._get_db()
        col = db["social_challenges"]
        challenge = col.find_one({"challenge_id": challenge_id}, {"participants": 1})
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        participants = challenge.get("participants", [])
        participant = next((p for p in participants if p["user_id"] == user_id), None)
        if not participant:
            raise ChallengeError("User not in challenge")
        new_score = max(0, int(participant.get("score", 0)) + score_delta)
        col.update_one(
            {"challenge_id": challenge_id, "participants.user_id": user_id},
            {"$set": {"participants.$.score": new_score}},
        )
        updated = col.find_one({"challenge_id": challenge_id}, {"participants": 1})
        sorted_p = sorted(
            updated.get("participants", []), key=lambda p: p.get("score", 0), reverse=True
        )
        current_rank = next(
            (i + 1 for i, p in enumerate(sorted_p) if p["user_id"] == user_id), 1
        )
        return new_score, current_rank

    @staticmethod
    def get_leaderboard(challenge_id: str, limit: int = 100, user_id: int = None) -> list:
        db = ChallengeService._get_db()
        challenge = db["social_challenges"].find_one(
            {"challenge_id": challenge_id}, {"participants": 1}
        )
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        sorted_p = sorted(
            challenge.get("participants", []),
            key=lambda p: p.get("score", 0),
            reverse=True,
        )[:limit]
        return [_entry(i + 1, p) for i, p in enumerate(sorted_p)]

    @staticmethod
    def cancel_challenge(challenge_id: str, user_id: int, reason: str = None) -> int:
        db = ChallengeService._get_db()
        challenge = db["social_challenges"].find_one(
            {"challenge_id": challenge_id}, {"participants": 1, "creator_id": 1}
        )
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        penalty = 0
        if challenge.get("creator_id") == user_id:
            db["social_challenges"].update_one(
                {"challenge_id": challenge_id},
                {"$set": {"status": "cancelled"}},
            )
        else:
            db["social_challenges"].update_one(
                {"challenge_id": challenge_id, "participants.user_id": user_id},
                {"$set": {"participants.$.is_active": False}},
            )
            penalty = 2
        return penalty

    @staticmethod
    def get_active_challenges(user_id: int, limit: int = 50) -> Tuple[list, int]:
        db = ChallengeService._get_db()
        now_iso = datetime.utcnow().isoformat()
        col = db["social_challenges"]
        match = {"status": "active", "end_time": {"$gte": now_iso}}
        total = col.count_documents(match)
        docs = list(
            col.find(match, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        # Ensure participants always have is_active field
        for doc in docs:
            for p in doc.get("participants", []):
                if "is_active" not in p:
                    p["is_active"] = True
        return docs, total
