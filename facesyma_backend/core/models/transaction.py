"""Transaction models for coin system"""
from enum import Enum


class TransactionType(Enum):
    """Types of coin transactions"""
    EARN_QUEST = "earn_quest"
    EARN_ACHIEVEMENT = "earn_achievement"
    EARN_CHALLENGE = "earn_challenge"
    SPEND_STAKE = "spend_stake"
    SPEND_PURCHASE = "spend_purchase"
    ADMIN_ADJUST = "admin_adjust"
    REFUND = "refund"
    DAILY_LOGIN = "daily_login"
    MEAL_GAME = "meal_game"
    DISCOVERY_GAME = "discovery_game"
    COACHING_QUEST = "coaching_quest"

    def __str__(self):
        return self.value


USER_COIN_FIELDS = {
    "coins": 0,
    "total_earned": 0,
    "total_spent": 0,
    "streak_count": 0,
    "last_daily_quest": None,
}
