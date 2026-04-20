"""
gamification/models/leaderboard_history.py
==========================================
Leaderboard trend analysis models.

Tracks: Daily leaderboard snapshots for trend analysis.
Enables: Rank history, progress tracking, achievement milestones.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LeaderboardSnapshot(BaseModel):
    """Single snapshot of leaderboard at a point in time"""

    user_id: int
    username: str
    rank: int
    coins_earned: int = Field(..., description="Total coins earned up to this snapshot")
    platinum_badges: int = Field(..., description="Count of platinum-tier badges")
    gold_and_above: int = Field(..., description="Count of gold+ tier badges")
    meals_completed: int = 0
    challenges_won: int = 0
    avg_accuracy: float = 0.0


class LeaderboardHistoryEntry(BaseModel):
    """Historical record of leaderboard state"""

    snapshot_id: str = Field(..., description="Unique snapshot ID (uuid)")
    snapshot_date: datetime = Field(..., description="When snapshot was taken")
    leaderboard_type: str = Field(..., description="'global', 'trait', or 'community'")
    trait_id: Optional[str] = None
    community_id: Optional[int] = None
    time_period: str = Field(default="all_time", description="'all_time', 'this_month', 'this_week'")
    sort_by: str = Field(default="coins", description="Sort metric used for snapshot")

    # Snapshot data
    total_users: int = Field(..., description="Total users in this leaderboard")
    top_10_entries: List[LeaderboardSnapshot] = Field(..., description="Top 10 users at time of snapshot")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When to delete this snapshot (for retention)")


class UserRankHistory(BaseModel):
    """User's rank progression over time"""

    user_id: int
    username: str
    leaderboard_type: str
    trait_id: Optional[str] = None
    community_id: Optional[int] = None

    # Timeline of rank changes
    snapshots: List[Dict[str, Any]] = Field(
        ...,
        description="[{date, rank, coins, badges, meals, challenges}, ...]"
    )


class RankTrendDataPoint(BaseModel):
    """Single data point in a user's rank trend"""

    snapshot_date: datetime
    rank: int
    coins_earned: int
    platinum_badges: int
    gold_and_above: int
    meals_completed: int
    challenges_won: int
    avg_accuracy: float

    class Config:
        json_schema_extra = {
            "example": {
                "snapshot_date": "2026-04-19T12:00:00Z",
                "rank": 45,
                "coins_earned": 2500,
                "platinum_badges": 2,
                "gold_and_above": 5,
                "meals_completed": 45,
                "challenges_won": 12,
                "avg_accuracy": 87.5
            }
        }


class UserTrendResponse(BaseModel):
    """User's trend data response"""

    user_id: int
    username: str
    leaderboard_type: str
    trait_id: Optional[str] = None
    community_id: Optional[int] = None

    # Current stats
    current_rank: Optional[int] = None
    current_coins: int = 0
    current_badges: int = 0

    # Trend data
    trend_days: int = Field(..., description="Number of days of history")
    trend_data: List[RankTrendDataPoint] = Field(
        ...,
        description="Daily snapshots (sorted by date ascending)"
    )

    # Calculated trends
    rank_change: int = Field(..., description="Change in rank (negative = better)")
    coins_gained: int = Field(..., description="Coins gained in period")
    badges_unlocked: int = Field(..., description="Badges unlocked in period")


class LeaderboardTrendComparison(BaseModel):
    """Compare two users' trends"""

    user1_id: int
    user2_id: int
    leaderboard_type: str

    user1_name: str
    user2_name: str

    # Current standings
    user1_rank: int
    user2_rank: int
    user1_coins: int
    user2_coins: int

    # Trends
    user1_rank_change: int
    user2_rank_change: int
    user1_momentum: str = Field(..., description="'ascending', 'stable', 'descending'")
    user2_momentum: str


class LeaderboardTrendStats(BaseModel):
    """Overall leaderboard trend statistics"""

    leaderboard_type: str
    snapshot_count: int = Field(..., description="Total snapshots recorded")
    days_tracked: int = Field(..., description="Days of history")

    # Most improved users (week)
    most_improved: List[Dict[str, Any]] = Field(
        ...,
        description="[{user_id, username, rank_change, coins_gained}, ...]"
    )

    # Most active users (week)
    most_active: List[Dict[str, Any]] = Field(
        ...,
        description="[{user_id, username, coins_earned, activities}, ...]"
    )

    # Volatility (rank churn)
    avg_rank_movement: float = Field(
        ...,
        description="Average daily rank change across all users"
    )
