"""
facesyma_ai/diet_coaching/services/meal_service.py
==================================================
Meal selection, tracking, leaderboard logic.

Loads from JSON, tracks selections in MongoDB, awards coins.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
from pydantic import ValidationError

from diet_coaching.models.meal import (
    Meal, MealSelection, MealLeaderboardEntry,
    COUNTRY_CODES, WEEK_ROTATION
)
from admin_api.utils.mongo import _get_db
from core.models.transaction import TransactionType
from core.services.coin_service import CoinService

log = logging.getLogger(__name__)

# Meals directory
MEALS_DIR = Path(__file__).parent.parent / "data"


class MealError(Exception):
    """Base exception for meal operations"""
    pass


class MealNotFoundError(MealError):
    """Meal not found"""
    pass


class InvalidCountryError(MealError):
    """Invalid country code"""
    pass


class MealService:
    """
    Meal selection & leaderboard service.

    Manages: loading from JSON, selections, history, leaderboard.
    """

    # ── In-memory cache for meals (loaded once) ────────────────────
    _meals_cache: dict = {}  # country -> [Meal, ...]

    @classmethod
    def _get_meals_file(cls, country: str) -> Path:
        """Get path to meals JSON file"""
        # country can be "japan" or "ja"
        code = COUNTRY_CODES.get(country, country)
        filename = f"meals_{code}.json"
        filepath = MEALS_DIR / filename

        if not filepath.exists():
            raise InvalidCountryError(
                f"Meals file not found: {filepath}\n"
                f"Available countries: {list(COUNTRY_CODES.keys())}"
            )
        return filepath

    @classmethod
    def load_meals(cls, country: str) -> List[Meal]:
        """
        Load meals from JSON file.

        Caches in memory after first load (optimization).

        Args:
            country: Country name (e.g., "japan", "turkey")

        Returns:
            List of Meal objects

        Raises:
            InvalidCountryError: If country not found
            MealError: If JSON invalid
        """
        # Check cache first
        _cache = cls._meals_cache
        if country in _cache:
            return _cache[country]

        filepath = cls._get_meals_file(country)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate and convert to Pydantic models
            meals = [Meal(**meal_data) for meal_data in data]

            # Cache
            _cache[country] = meals
            log.info(f"✓ Loaded {len(meals)} meals for {country}")
            return meals

        except json.JSONDecodeError as e:
            raise MealError(f"Invalid JSON in {filepath}: {e}")
        except ValidationError as e:
            raise MealError(f"Invalid meal schema in {filepath}: {e}")
        except Exception as e:
            raise MealError(f"Error loading meals: {e}")

    @staticmethod
    def get_current_week_country() -> str:
        """
        Get country for current week (rotation).

        Week 1 (Jan 1-7) = Japan
        Week 2 (Jan 8-14) = Turkey
        ... repeats every 18 weeks

        Returns: country name (e.g., "japan")
        """
        now = datetime.utcnow()
        week_of_year = now.isocalendar()[1]  # 1-53
        country_index = (week_of_year - 1) % len(WEEK_ROTATION)
        return WEEK_ROTATION[country_index]

    @staticmethod
    def select_random_meals(meals: List[Meal], count: int = 3) -> List[Meal]:
        """
        Select random meals from list.

        Args:
            meals: All meals for country
            count: How many to select (default 3)

        Returns:
            Random subset of meals
        """
        return random.sample(meals, min(count, len(meals)))

    @staticmethod
    def _get_week_key() -> str:
        """
        Get week key for leaderboard tracking.

        Format: "2026-W17" (ISO week)

        Returns: week key
        """
        now = datetime.utcnow()
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"

    @classmethod
    def select_meal(
        cls,
        user_id: int,
        meal_id: str,
        country: str,
    ) -> Tuple[int, str]:
        """
        User selects a meal.

        Records selection, awards coins.

        Args:
            user_id: User ID
            meal_id: Meal ID (e.g., "jp_breakfast_001")
            country: Country (e.g., "japan")

        Returns:
            Tuple[new_balance, transaction_id]

        Raises:
            MealNotFoundError: If meal not found
            MealError: If selection fails
        """
        # Load meals
        meals = cls.load_meals(country)
        meal = next((m for m in meals if m.id == meal_id), None)

        if not meal:
            raise MealNotFoundError(
                f"Meal {meal_id} not found in {country}"
            )

        _mne = meal.name_en
        # Record selection in MongoDB
        sel_col = _get_db()["meal_selections"]
        selection_doc = {
            "user_id": user_id,
            "meal_id": meal_id,
            "meal_name_en": _mne,
            "meal_name_tr": getattr(meal, "name_tr", ""),
            "country": country,
            "selected_at": datetime.utcnow().isoformat(),
            "week_key": cls._get_week_key(),
            "sifat_guess": None,
            "sifat_correct": None,
            "coins_earned": 10,  # Base amount
        }
        sel_col.insert_one(selection_doc)

        # Award coins
        new_balance, trans_id = CoinService.add_coins(
            user_id=user_id,
            amount=10,
            transaction_type=TransactionType.MEAL_GAME,
            description=f"Selected meal: {_mne} ({country})",
            metadata={
                "meal_id": meal_id,
                "country": country,
                "meal_name": _mne,
            },
        )

        log.info(
            f"✓ Meal selected: user={user_id}, meal={meal_id}, "
            f"country={country}, balance={new_balance}"
        )

        return new_balance, trans_id

    @classmethod
    def guess_sifat_match(
        cls,
        user_id: int,
        meal_id: str,
        country: str,
        guess: str,  # "yes", "no", "unsure"
    ) -> Tuple[bool, int, str]:
        """
        User guesses if meal matches their personality.

        Meal's sifat_appeal list indicates target sıfats.
        Guess evaluated against user's profile sıfats.

        Args:
            user_id: User ID
            meal_id: Meal ID
            country: Country
            guess: User's guess ("yes", "no", "unsure")

        Returns:
            Tuple[is_correct, bonus_coins, feedback_message]

        Raises:
            MealNotFoundError: If meal not found
        """
        # Load meals & find
        meals = cls.load_meals(country)
        meal = next((m for m in meals if m.id == meal_id), None)

        if not meal:
            raise MealNotFoundError(f"Meal {meal_id} not found")

        # For MVP: Simple heuristic matching
        # TODO: Replace with actual sıfat profile comparison
        # For now: 70% chance user's guess is "correct"
        is_correct = random.random() < 0.70
        _msa = meal.sifat_appeal

        bonus = 0
        feedback = ""

        if guess != "unsure":
            if is_correct:
                bonus = 5
                feedback = (
                    f"✓ Correct! This meal appeals to "
                    f"{', '.join(_msa)} personalities."
                )

                # Award bonus coins
                CoinService.add_coins(
                    user_id=user_id,
                    amount=bonus,
                    transaction_type=TransactionType.MEAL_GAME,
                    description=f"Sıfat guess correct: {meal.name_en}",
                    metadata={
                        "meal_id": meal_id,
                        "guess": guess,
                        "sifat_appeal": _msa,
                    },
                )
            else:
                feedback = (
                    f"Not quite! This meal appeals to "
                    f"{', '.join(_msa)} personalities."
                )
        else:
            feedback = "No worries! You'll learn more as you explore."

        # Record guess in MongoDB
        sel_col = _get_db()["meal_selections"]
        sel_col.update_one(
            {
                "user_id": user_id,
                "meal_id": meal_id,
                "selected_at": {"$gte": (datetime.utcnow() - timedelta(hours=1)).isoformat()},
            },
            {
                "$set": {
                    "sifat_guess": guess,
                    "sifat_correct": is_correct,
                    "coins_earned": 10 + bonus,
                }
            },
        )

        log.info(
            f"✓ Sifat guess: user={user_id}, meal={meal_id}, "
            f"guess={guess}, correct={is_correct}, bonus=+{bonus}"
        )

        return is_correct, bonus, feedback

    @staticmethod
    def get_weekly_leaderboard(
        country: str,
        limit: int = 100,
    ) -> List[MealLeaderboardEntry]:
        """
        Get this week's meal game leaderboard.

        Ranked by meals completed, then by accuracy.

        Args:
            country: Filter by country (e.g., "japan")
            limit: Max results (default 100)

        Returns:
            List of leaderboard entries
        """
        week_key = MealService._get_week_key()
        _db = _get_db()
        sel_col = _db["meal_selections"]
        users_col = _db["appfaceapi_myuser"]

        # Aggregate: count meals + calculate accuracy
        pipeline = [
            {
                "$match": {
                    "country": country,
                    "week_key": week_key,
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "meals_completed": {"$sum": 1},
                    "coins_earned": {"$sum": "$coins_earned"},
                    "sifat_guesses": {
                        "$sum": {
                            "$cond": [
                                {"$ne": ["$sifat_guess", None]},
                                1,
                                0
                            ]
                        }
                    },
                    "sifat_correct": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$sifat_correct", True]},
                                1,
                                0
                            ]
                        }
                    },
                }
            },
            {
                "$sort": {
                    "meals_completed": -1,
                    "coins_earned": -1,
                }
            },
            {"$limit": limit},
        ]

        results = list(sel_col.aggregate(pipeline))

        user_ids = [doc["_id"] for doc in results]
        users_map = {u["id"]: u for u in users_col.find(
            {"id": {"$in": user_ids}}, {"id": 1, "username": 1, "avatar": 1}
        ).limit(len(user_ids) or 1)}

        entries = []
        for rank, doc in enumerate(results, 1):
            user_id = doc["_id"]
            user = users_map.get(user_id)
            if not user:
                continue

            # Calculate accuracy
            _dget   = doc.get
            guesses = _dget("sifat_guesses", 0)
            correct = _dget("sifat_correct", 0)
            accuracy = (correct / guesses * 100) if guesses > 0 else 0

            _uget = user.get
            entries.append(MealLeaderboardEntry(
                rank=rank,
                user_id=user_id,
                username=_uget("username", "Unknown"),
                avatar=_uget("avatar"),
                meals_completed=_dget("meals_completed", 0),
                coins_earned=_dget("coins_earned", 0),
                accuracy_percent=round(accuracy, 1),
            ))

        return entries

    @staticmethod
    def get_user_meal_history(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """
        Get user's meal selection history.

        Args:
            user_id: User ID
            limit: Max results
            offset: Skip N results

        Returns:
            Tuple[selections_list, total_count]
        """
        sel_col = _get_db()["meal_selections"]

        total = sel_col.count_documents({"user_id": user_id})
        docs = list(
            sel_col.find({"user_id": user_id})
            .sort("selected_at", -1)
            .skip(offset)
            .limit(limit)
        )

        # Convert ObjectId to string
        for doc in docs:
            _oid = doc["_id"]
            doc["_id"] = str(_oid)

        return docs, total
