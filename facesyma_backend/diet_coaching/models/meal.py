"""Meal models for the meal game."""

from typing import Optional, List, Dict


class Nutrition:
    __slots__ = ('calories', 'protein', 'carbs', 'fat')

    def __init__(self, calories: int = 0, protein: int = 0, carbs: int = 0, fat: int = 0):
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat


class Dietary:
    __slots__ = ('omnivore', 'vegetarian', 'vegan', 'gluten_free')

    def __init__(self, omnivore: bool = True, vegetarian: bool = False,
                 vegan: bool = False, gluten_free: bool = False):
        self.omnivore = omnivore
        self.vegetarian = vegetarian
        self.vegan = vegan
        self.gluten_free = gluten_free


class Meal:
    __slots__ = (
        'id', 'name_en', 'name_tr', 'description',
        'nutrition', 'dietary', 'prep_time_min',
        'sifat_appeal', 'season', 'frequency_weight',
    )

    def __init__(
        self,
        id: str,
        name_en: str,
        name_tr: str,
        description: str = '',
        nutrition: Optional[Nutrition] = None,
        dietary: Optional[Dietary] = None,
        prep_time_min: int = 15,
        sifat_appeal: Optional[List[str]] = None,
        season: str = 'year_round',
        frequency_weight: float = 1.0,
    ):
        self.id = id
        self.name_en = name_en
        self.name_tr = name_tr
        self.description = description
        self.nutrition = nutrition or Nutrition()
        self.dietary = dietary or Dietary()
        self.prep_time_min = prep_time_min
        self.sifat_appeal = sifat_appeal or []
        self.season = season
        self.frequency_weight = frequency_weight


class MealSelectionRequest:
    __slots__ = ('user_id', 'meal_id', 'country', 'metadata')

    def __init__(self, user_id: int, meal_id: str, country: str, metadata: Optional[Dict] = None):
        self.user_id = user_id
        self.meal_id = meal_id
        self.country = country
        self.metadata = metadata or {}


class MealSifatGuessRequest:
    __slots__ = ('user_id', 'meal_id', 'country', 'guess')

    def __init__(self, user_id: int, meal_id: str, country: str, guess: str):
        self.user_id = user_id
        self.meal_id = meal_id
        self.country = country
        self.guess = guess


class MealLeaderboardEntry:
    __slots__ = ('rank', 'user_id', 'username', 'avatar', 'meals_completed', 'coins_earned', 'accuracy_percent')

    def __init__(
        self,
        rank: int,
        user_id: int,
        username: str,
        meals_completed: int,
        coins_earned: int,
        accuracy_percent: float = 0.0,
        avatar: Optional[str] = None,
    ):
        self.rank = rank
        self.user_id = user_id
        self.username = username
        self.avatar = avatar
        self.meals_completed = meals_completed
        self.coins_earned = coins_earned
        self.accuracy_percent = accuracy_percent


COUNTRY_CODES: Dict[str, str] = {
    'TR': 'Türkiye', 'US': 'United States', 'GB': 'United Kingdom',
    'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain',
    'PT': 'Portugal', 'NL': 'Netherlands', 'BE': 'Belgium',
    'CH': 'Switzerland', 'GR': 'Greece', 'PL': 'Poland',
    'JP': 'Japan', 'KR': 'South Korea', 'IN': 'India',
    'CN': 'China', 'TH': 'Thailand', 'MY': 'Malaysia',
    'PH': 'Philippines', 'ID': 'Indonesia',
    'BR': 'Brazil', 'MX': 'Mexico', 'AU': 'Australia',
    'CA': 'Canada', 'ZA': 'South Africa', 'NG': 'Nigeria',
    'KE': 'Kenya', 'ET': 'Ethiopia', 'IL': 'Israel',
    'IR': 'Iran', 'SA': 'Saudi Arabia', 'TW': 'Taiwan',
}

__all__ = [
    'Nutrition', 'Dietary', 'Meal',
    'MealSelectionRequest', 'MealSifatGuessRequest',
    'MealLeaderboardEntry', 'COUNTRY_CODES',
]
