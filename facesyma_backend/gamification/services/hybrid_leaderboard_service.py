"""Hybrid leaderboard service — MongoDB-backed global/trait/community leaderboards."""
from datetime import datetime
from gamification.models.leaderboard import (
    LeaderboardFilter, LeaderboardEntry, LeaderboardResult,
)


class LeaderboardError(Exception):
    pass


_SORT_FIELD_MAP = {
    "coins": "coins",
    "rank": "coins",
    "badges": "total_badges",
    "accuracy": "avg_accuracy",
    "name": "username",
}


def _period_filter(time_period: str) -> dict:
    from datetime import timedelta
    if time_period == "all_time":
        return {}
    now = datetime.utcnow()
    days = {"7d": 7, "30d": 30, "90d": 90, "monthly": 30}.get(time_period, 0)
    if not days:
        return {}
    cutoff = (now - timedelta(days=days)).isoformat()
    return {"date_joined": {"$gte": cutoff}}


def _build_entry(doc: dict, rank: int) -> LeaderboardEntry:
    uid = doc.get("id") or doc.get("user_id")
    return LeaderboardEntry(
        rank=rank,
        user_id=uid,
        username=doc.get("username", f"user_{uid}"),
        avatar=doc.get("avatar"),
        coins_balance=int(doc.get("coins", 0)),
        total_coins_earned=int(doc.get("total_earned", 0)),
        platinum_badges=int(doc.get("platinum_badges", 0)),
        gold_and_above=int(doc.get("gold_and_above", 0)),
        meals_completed=int(doc.get("meals_completed", 0)),
        challenges_won=int(doc.get("challenges_won", 0)),
        avg_accuracy=float(doc.get("avg_accuracy", 0.0)),
        top_traits=doc.get("top_sifats", []),
    )


class HybridLeaderboardService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def _query_leaderboard(
        match: dict,
        sort_by: str,
        limit: int,
        offset: int,
        user_id: int,
        lb_type: str,
        lb_name: str,
        time_period: str,
    ) -> LeaderboardResult:
        db = HybridLeaderboardService._db()
        col = db["appfaceapi_myuser"]
        sort_field = _SORT_FIELD_MAP.get(sort_by, "coins")
        total = col.count_documents(match)
        docs = list(
            col.find(match, {"_id": 0, "password": 0, "email": 0})
            .sort(sort_field, -1)
            .skip(offset)
            .limit(limit)
        )
        entries = [_build_entry(doc, offset + i + 1) for i, doc in enumerate(docs)]
        user_rank = None
        if user_id:
            above = col.count_documents({**match, sort_field: {"$gt": next(
                (doc.get(sort_field, 0) for doc in docs
                 if (doc.get("id") or doc.get("user_id")) == user_id), 0
            )}})
            user_rank = above + 1
        return LeaderboardResult(
            leaderboard_type=lb_type,
            leaderboard_name=lb_name,
            time_period=time_period,
            sort_by=sort_by,
            total_entries=total,
            user_rank=user_rank,
            cached=False,
            cache_expiry=None,
            entries=entries,
        )

    @staticmethod
    def get_hybrid_leaderboard(
        filter_params: LeaderboardFilter,
        user_id: int,
    ) -> LeaderboardResult:
        lt = filter_params.leaderboard_type
        if lt == "trait":
            return HybridLeaderboardService.get_trait_leaderboard(
                trait_id=filter_params.trait_id,
                time_period=filter_params.time_period,
                sort_by=filter_params.sort_by,
                limit=filter_params.limit,
                offset=filter_params.offset,
                user_id=user_id,
            )
        if lt == "community":
            return HybridLeaderboardService.get_community_leaderboard(
                community_id=filter_params.community_id,
                time_period=filter_params.time_period,
                sort_by=filter_params.sort_by,
                limit=filter_params.limit,
                offset=filter_params.offset,
                user_id=user_id,
            )
        return HybridLeaderboardService.get_global_leaderboard(
            time_period=filter_params.time_period,
            sort_by=filter_params.sort_by,
            limit=filter_params.limit,
            offset=filter_params.offset,
            user_id=user_id,
        )

    @staticmethod
    def get_global_leaderboard(
        time_period: str = "all_time",
        sort_by: str = "coins",
        limit: int = 100,
        offset: int = 0,
        user_id: int = None,
    ) -> LeaderboardResult:
        match = _period_filter(time_period)
        return HybridLeaderboardService._query_leaderboard(
            match, sort_by, limit, offset, user_id,
            "global", "Global Leaderboard", time_period,
        )

    @staticmethod
    def get_trait_leaderboard(
        trait_id: str = None,
        time_period: str = "all_time",
        sort_by: str = "coins",
        limit: int = 100,
        offset: int = 0,
        user_id: int = None,
    ) -> LeaderboardResult:
        match = _period_filter(time_period)
        if trait_id:
            match["top_sifats"] = trait_id
        lb_name = f"Trait Leaderboard: {trait_id}" if trait_id else "Trait Leaderboard"
        return HybridLeaderboardService._query_leaderboard(
            match, sort_by, limit, offset, user_id,
            "trait", lb_name, time_period,
        )

    @staticmethod
    def get_community_leaderboard(
        community_id: int = None,
        time_period: str = "all_time",
        sort_by: str = "coins",
        limit: int = 100,
        offset: int = 0,
        user_id: int = None,
    ) -> LeaderboardResult:
        db = HybridLeaderboardService._db()
        match = _period_filter(time_period)
        if community_id:
            community = db["communities"].find_one(
                {"_id": community_id}, {"members": 1}
            )
            if community:
                member_ids = [m.get("user_id") for m in community.get("members", [])]
                match["id"] = {"$in": member_ids}
        lb_name = f"Community #{community_id}" if community_id else "Community Leaderboard"
        return HybridLeaderboardService._query_leaderboard(
            match, sort_by, limit, offset, user_id,
            "community", lb_name, time_period,
        )
