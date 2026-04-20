"""Coin service for managing user coins and transactions"""
from typing import Optional, Dict, Any


class CoinError(Exception):
    """Base exception for coin service errors"""
    pass


class InsufficientCoinsError(CoinError):
    """Raised when user doesn't have enough coins"""
    pass


class InvalidAmountError(CoinError):
    """Raised when an invalid amount is provided"""
    pass


class CoinService:
    """Service for managing coin operations"""

    def get_balance(self, user_id: int) -> int:
        """Get user's current coin balance"""
        return 0

    def add_coins(
        self,
        user_id: int,
        amount: int,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Add coins to user"""
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive")
        return {
            'user_id': user_id,
            'amount': amount,
            'reason': reason,
            'new_balance': 0
        }

    def deduct_coins(
        self,
        user_id: int,
        amount: int,
        reason: str
    ) -> Dict[str, Any]:
        """Deduct coins from user"""
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive")
        return {
            'user_id': user_id,
            'amount': amount,
            'reason': reason,
            'new_balance': 0
        }

    def get_history(self, user_id: int, limit: int = 50) -> list:
        """Get user's coin transaction history"""
        return []
