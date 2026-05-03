"""Leaderboard models — filter and response classes."""
from datetime import datetime
from typing import List, Optional


class LeaderboardFilter:
    __slots__ = (
        "leaderboard_type", "trait_id", "community_id",
        "time_period", "sort_by", "limit", "offset",
    )

    def __init__(
        self,
        leaderboard_type: str = "global",
        trait_id: Optional[str] = None,
        community_id: Optional[int] = None,
        time_period: str = "all_time",
        sort_by: str = "coins",
        limit: int = 100,
        offset: int = 0,
    ):
        self.leaderboard_type = leaderboard_type
        self.trait_id = trait_id
        self.community_id = community_id
        self.time_period = time_period
        self.sort_by = sort_by
        self.limit = limit
        self.offset = offset


class LeaderboardEntry:
    __slots__ = (
        "rank", "user_id", "username", "avatar",
        "coins_balance", "total_coins_earned",
        "platinum_badges", "gold_and_above",
        "meals_completed", "challenges_won",
        "avg_accuracy", "top_traits",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class LeaderboardResult:
    __slots__ = (
        "leaderboard_type", "leaderboard_name",
        "time_period", "sort_by",
        "total_entries", "user_rank",
        "cached", "cache_expiry",
        "entries",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class TrendPoint:
    __slots__ = (
        "snapshot_date", "rank",
        "coins_earned", "platinum_badges", "gold_and_above",
        "meals_completed", "challenges_won", "avg_accuracy",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


class TrendResponse:
    __slots__ = (
        "user_id", "username",
        "leaderboard_type", "trait_id", "community_id",
        "current_rank", "current_coins", "current_badges",
        "trend_days", "rank_change", "coins_gained", "badges_unlocked",
        "trend_data",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))
