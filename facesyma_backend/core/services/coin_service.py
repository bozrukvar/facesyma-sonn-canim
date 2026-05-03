"""Coin service — MongoDB-backed coin and transaction management."""
from datetime import datetime
from typing import Optional, Tuple, List


class CoinError(Exception):
    pass


class InsufficientCoinsError(CoinError):
    pass


class InvalidAmountError(CoinError):
    pass


class CoinService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def get_balance(user_id: int) -> int:
        user = CoinService._db()["appfaceapi_myuser"].find_one(
            {"id": user_id}, {"coins": 1, "_id": 0}
        )
        if not user:
            raise CoinError(f"User {user_id} not found")
        return int(user.get("coins", 0))

    @staticmethod
    def get_stats(user_id: int) -> dict:
        user = CoinService._db()["appfaceapi_myuser"].find_one(
            {"id": user_id},
            {"coins": 1, "total_earned": 1, "total_spent": 1,
             "streak_count": 1, "last_daily_quest": 1, "_id": 0},
        )
        if not user:
            raise CoinError(f"User {user_id} not found")
        return {
            "current_balance": int(user.get("coins", 0)),
            "total_earned": int(user.get("total_earned", 0)),
            "total_spent": int(user.get("total_spent", 0)),
            "streak_days": int(user.get("streak_count", 0)),
            "last_daily_quest": user.get("last_daily_quest"),
        }

    @staticmethod
    def get_transaction_history(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        col = CoinService._db()["coin_transactions"]
        query = {"user_id": user_id}
        if transaction_type:
            query["type"] = transaction_type
        total = col.count_documents(query)
        docs = list(
            col.find(query, {"_id": 0})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return docs, total

    @staticmethod
    def add_coins(
        user_id: int,
        amount: int,
        transaction_type,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> Tuple[int, str]:
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive")
        db = CoinService._db()
        result = db["appfaceapi_myuser"].find_one_and_update(
            {"id": user_id},
            {"$inc": {"coins": amount, "total_earned": amount},
             "$setOnInsert": {"total_spent": 0, "streak_count": 0}},
            return_document=True,
            projection={"coins": 1, "_id": 0},
            upsert=False,
        )
        if not result:
            raise CoinError(f"User {user_id} not found")
        new_balance = int(result.get("coins", 0))
        res = db["coin_transactions"].insert_one({
            "user_id": user_id,
            "amount": amount,
            "type": str(transaction_type),
            "description": description,
            "balance_after": new_balance,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        })
        return new_balance, str(res.inserted_id)

    @staticmethod
    def deduct_coins(
        user_id: int,
        amount: int,
        transaction_type,
        description: str = "",
        metadata: Optional[dict] = None,
        allow_negative: bool = False,
    ) -> Tuple[int, str]:
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive")
        db = CoinService._db()
        if not allow_negative:
            user = db["appfaceapi_myuser"].find_one({"id": user_id}, {"coins": 1})
            if not user:
                raise CoinError(f"User {user_id} not found")
            if int(user.get("coins", 0)) < amount:
                raise InsufficientCoinsError(
                    f"Need {amount}, have {user.get('coins', 0)}"
                )
        result = db["appfaceapi_myuser"].find_one_and_update(
            {"id": user_id},
            {"$inc": {"coins": -amount, "total_spent": amount}},
            return_document=True,
            projection={"coins": 1, "_id": 0},
        )
        if not result:
            raise CoinError(f"User {user_id} not found")
        new_balance = int(result.get("coins", 0))
        res = db["coin_transactions"].insert_one({
            "user_id": user_id,
            "amount": -amount,
            "type": str(transaction_type),
            "description": description,
            "balance_after": new_balance,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        })
        return new_balance, str(res.inserted_id)

    @staticmethod
    def update_daily_quest_streak(user_id: int) -> int:
        db = CoinService._db()
        user = db["appfaceapi_myuser"].find_one(
            {"id": user_id}, {"last_daily_quest": 1, "streak_count": 1, "_id": 0}
        )
        if not user:
            raise CoinError(f"User {user_id} not found")
        now = datetime.utcnow()
        last_str = user.get("last_daily_quest")
        streak = int(user.get("streak_count", 0))
        if last_str:
            try:
                last_dt = datetime.fromisoformat(last_str)
                diff = (now.date() - last_dt.date()).days
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
    def admin_adjust_coins(
        user_id: int,
        amount: int,
        reason: str,
        admin_id,
    ) -> Tuple[int, str]:
        from core.models.transaction import TransactionType
        db = CoinService._db()
        if amount == 0:
            user = db["appfaceapi_myuser"].find_one({"id": user_id}, {"coins": 1})
            if not user:
                raise CoinError(f"User {user_id} not found")
            new_balance = int(user.get("coins", 0))
        elif amount > 0:
            result = db["appfaceapi_myuser"].find_one_and_update(
                {"id": user_id},
                {"$inc": {"coins": amount, "total_earned": amount}},
                return_document=True,
                projection={"coins": 1, "_id": 0},
            )
            if not result:
                raise CoinError(f"User {user_id} not found")
            new_balance = int(result.get("coins", 0))
        else:
            result = db["appfaceapi_myuser"].find_one_and_update(
                {"id": user_id},
                {"$inc": {"coins": amount, "total_spent": -amount}},
                return_document=True,
                projection={"coins": 1, "_id": 0},
            )
            if not result:
                raise CoinError(f"User {user_id} not found")
            new_balance = int(result.get("coins", 0))
        res = db["coin_transactions"].insert_one({
            "user_id": user_id,
            "amount": amount,
            "type": str(TransactionType.ADMIN_ADJUST),
            "description": reason,
            "balance_after": new_balance,
            "metadata": {"admin_id": str(admin_id)},
            "created_at": datetime.utcnow().isoformat(),
        })
        return new_balance, str(res.inserted_id)
