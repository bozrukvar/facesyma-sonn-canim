"""Leaderboard trend service — snapshot storage and trend analysis."""
import random
import string
from datetime import datetime, timedelta
from types import SimpleNamespace
from gamification.models.leaderboard import TrendPoint, TrendResponse


class TrendError(Exception):
    pass


class TrendNotFoundError(TrendError):
    pass


class SnapshotError(TrendError):
    pass


class LeaderboardTrendService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def take_snapshot(
        leaderboard_type: str = "global",
        trait_id: str = None,
        community_id=None,
        time_period: str = "all_time",
        sort_by: str = "coins",
        top_n: int = 100,
    ) -> str:
        db = LeaderboardTrendService._db()
        users_col = db["appfaceapi_myuser"]
        snapshots_col = db["leaderboard_snapshots"]
        now = datetime.utcnow()

        match = {}
        if leaderboard_type == "trait" and trait_id:
            match["top_sifats"] = trait_id
        elif leaderboard_type == "community" and community_id:
            community = db["communities"].find_one(
                {"_id": community_id}, {"members": 1}
            )
            if community:
                match["id"] = {"$in": [m.get("user_id") for m in community.get("members", [])]}

        sort_field = {"coins": "coins", "rank": "coins", "badges": "total_badges"}.get(sort_by, "coins")
        docs = list(
            users_col.find(match, {"id": 1, "username": 1, "coins": 1, "total_earned": 1, "_id": 0})
            .sort(sort_field, -1)
            .limit(top_n)
        )
        entries = [
            {
                "rank": i + 1,
                "user_id": d.get("id"),
                "username": d.get("username", f"user_{d.get('id')}"),
                "coins": int(d.get("coins", 0)),
                "total_earned": int(d.get("total_earned", 0)),
            }
            for i, d in enumerate(docs)
        ]
        snapshot_id = "snap_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        snapshots_col.insert_one({
            "snapshot_id": snapshot_id,
            "leaderboard_type": leaderboard_type,
            "trait_id": trait_id,
            "community_id": community_id,
            "time_period": time_period,
            "sort_by": sort_by,
            "entries": entries,
            "taken_at": now.isoformat(),
            "taken_at_ts": now.timestamp(),
        })
        return snapshot_id

    @staticmethod
    def cleanup_old_snapshots(days: int = 90) -> int:
        db = LeaderboardTrendService._db()
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = db["leaderboard_snapshots"].delete_many({"taken_at": {"$lt": cutoff}})
        return result.deleted_count

    @staticmethod
    def cleanup_old_snapshots_alias():
        return LeaderboardTrendService.cleanup_old_snapshots()

    @staticmethod
    def get_user_trend(
        user_id: int,
        leaderboard_type: str = "global",
        trait_id: str = None,
        community_id=None,
        days: int = 30,
    ) -> TrendResponse:
        db = LeaderboardTrendService._db()
        snapshots_col = db["leaderboard_snapshots"]
        users_col = db["appfaceapi_myuser"]
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        match = {
            "leaderboard_type": leaderboard_type,
            "taken_at": {"$gte": cutoff},
        }
        if trait_id:
            match["trait_id"] = trait_id
        if community_id:
            match["community_id"] = community_id
        snapshots = list(snapshots_col.find(match, {"_id": 0}).sort("taken_at", 1))
        user = users_col.find_one(
            {"id": user_id}, {"username": 1, "coins": 1, "total_badges": 1, "_id": 0}
        )
        if not user:
            raise TrendNotFoundError(f"User {user_id} not found")
        trend_data = []
        for snap in snapshots:
            entry = next((e for e in snap.get("entries", []) if e.get("user_id") == user_id), None)
            if entry:
                try:
                    snap_date = datetime.fromisoformat(snap["taken_at"])
                except Exception:
                    snap_date = datetime.utcnow()
                trend_data.append(TrendPoint(
                    snapshot_date=snap_date,
                    rank=entry.get("rank"),
                    coins_earned=entry.get("coins", 0),
                    platinum_badges=0,
                    gold_and_above=0,
                    meals_completed=0,
                    challenges_won=0,
                    avg_accuracy=0.0,
                ))
        rank_change = 0
        coins_gained = 0
        badges_unlocked = 0
        if len(trend_data) >= 2:
            rank_change = (trend_data[0].rank or 0) - (trend_data[-1].rank or 0)
            coins_gained = (trend_data[-1].coins_earned or 0) - (trend_data[0].coins_earned or 0)
        current_rank = trend_data[-1].rank if trend_data else None
        return TrendResponse(
            user_id=user_id,
            username=user.get("username", f"user_{user_id}"),
            leaderboard_type=leaderboard_type,
            trait_id=trait_id,
            community_id=community_id,
            current_rank=current_rank,
            current_coins=int(user.get("coins", 0)),
            current_badges=int(user.get("total_badges", 0)),
            trend_days=days,
            rank_change=rank_change,
            coins_gained=coins_gained,
            badges_unlocked=badges_unlocked,
            trend_data=trend_data,
        )

    @staticmethod
    def get_trending_users(
        leaderboard_type: str = "global",
        days: int = 7,
        limit: int = 20,
        metric: str = "rank_improvement",
        sort_by: str = None,
        min_snapshots: int = 2,
        time_window_days: int = None,
    ) -> list:
        effective_days = time_window_days if time_window_days is not None else days
        effective_sort = sort_by or metric
        db = LeaderboardTrendService._db()
        cutoff = (datetime.utcnow() - timedelta(days=effective_days)).isoformat()
        snapshots = list(
            db["leaderboard_snapshots"].find(
                {"leaderboard_type": leaderboard_type, "taken_at": {"$gte": cutoff}},
                {"_id": 0, "entries": 1, "taken_at": 1},
            ).sort("taken_at", 1)
        )
        if len(snapshots) < 2:
            return []
        first_snap = snapshots[0]
        last_snap = snapshots[-1]
        first_map = {e["user_id"]: e for e in first_snap.get("entries", [])}
        last_map = {e["user_id"]: e for e in last_snap.get("entries", [])}
        trending = []
        for uid, last in last_map.items():
            first = first_map.get(uid)
            if not first:
                continue
            rank_improvement = first.get("rank", 9999) - last.get("rank", 9999)
            coins_gained = last.get("coins", 0) - first.get("coins", 0)
            trending.append({
                "user_id": uid,
                "username": last.get("username", f"user_{uid}"),
                "rank_improvement": rank_improvement,
                "coins_gained": coins_gained,
                "current_rank": last.get("rank"),
            })
        key_fn = {
            "rank_improvement": lambda x: x["rank_improvement"],
            "coins_gained": lambda x: x["coins_gained"],
        }.get(effective_sort, lambda x: x["rank_improvement"])
        trending.sort(key=key_fn, reverse=True)
        return trending[:limit]

    @staticmethod
    def get_leaderboard_stats(
        leaderboard_type: str = "global",
        days: int = 7,
    ):
        db = LeaderboardTrendService._db()
        users_col = db["appfaceapi_myuser"]
        total_users = users_col.count_documents({})
        pipeline = [
            {"$group": {"_id": None, "avg_coins": {"$avg": "$coins"}, "max_coins": {"$max": "$coins"}}},
        ]
        agg = next(users_col.aggregate(pipeline), {})
        snap_col = db["leaderboard_snapshots"]
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        snapshots_count = snap_col.count_documents(
            {"leaderboard_type": leaderboard_type, "taken_at": {"$gte": cutoff}}
        )
        trending = LeaderboardTrendService.get_trending_users(
            leaderboard_type=leaderboard_type, days=days, limit=10
        )
        most_improved = [
            {"user_id": t["user_id"], "username": t["username"],
             "rank_change": t["rank_improvement"], "coins_gained": t["coins_gained"]}
            for t in trending[:10]
        ]
        most_active = sorted(
            [{"user_id": t["user_id"], "username": t["username"],
              "coins_earned": t["coins_gained"]}
             for t in trending],
            key=lambda x: x["coins_earned"],
            reverse=True,
        )[:10]
        return SimpleNamespace(
            leaderboard_type=leaderboard_type,
            total_users=total_users,
            avg_coins=round(float(agg.get("avg_coins") or 0), 2),
            max_coins=int(agg.get("max_coins") or 0),
            snapshot_count=snapshots_count,
            days_tracked=days,
            avg_rank_movement=0.0,
            most_improved=most_improved,
            most_active=most_active,
        )
