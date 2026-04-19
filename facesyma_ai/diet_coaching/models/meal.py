"""
facesyma_ai/diet_coaching/models/meal.py
========================================
Pydantic models for meal data validation & serialization.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class NutritionInfo(BaseModel):
    """Nutritional information per meal"""
    calories: int = Field(..., ge=50, le=1500, description="Kilocalories")
    protein: int = Field(..., ge=0, le=100, description="Grams")
    carbs: int = Field(..., ge=0, le=200, description="Grams")
    fat: int = Field(..., ge=0, le=100, description="Grams")


class DietaryPreferences(BaseModel):
    """Dietary flags for filtering"""
    omnivore: bool = True
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False


class Meal(BaseModel):
    """
    Meal document from JSON files.

    Example:
    {
        "id": "jp_breakfast_001",
        "name_tr": "Miso Soup",
        "name_en": "Miso Soup",
        "description": "Traditional Japanese...",
        "nutrition": {
            "calories": 180,
            "protein": 8,
            "carbs": 12,
            "fat": 6
        },
        "prep_time_min": 15,
        "dietary": {
            "omnivore": true,
            "vegetarian": true,
            "vegan": false,
            "gluten_free": true
        },
        "vegan_substitute": "Use vegetable broth...",
        "sifat_appeal": ["rahat", "saglikli", "dogu"],
        "season": "year_round",
        "frequency_weight": 0.95
    }
    """
    id: str
    name_tr: str
    name_en: str
    description: str
    nutrition: NutritionInfo
    prep_time_min: int = Field(..., ge=5, le=180)
    dietary: DietaryPreferences
    vegan_substitute: str
    sifat_appeal: List[str]  # e.g., ["rahat", "saglikli"]
    season: Literal[
        "year_round", "summer", "winter", "spring", "autumn"
    ] = "year_round"
    frequency_weight: float = Field(..., ge=0.5, le=1.2)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tr_breakfast_001",
                "name_tr": "Menemen",
                "name_en": "Turkish Scrambled Eggs",
                "description": "Scrambled eggs with tomatoes and peppers...",
                "nutrition": {
                    "calories": 280,
                    "protein": 16,
                    "carbs": 12,
                    "fat": 18
                },
                "prep_time_min": 20,
                "dietary": {
                    "omnivore": True,
                    "vegetarian": True,
                    "vegan": False,
                    "gluten_free": True
                },
                "vegan_substitute": "Use tofu instead of eggs...",
                "sifat_appeal": ["tatli", "saglikli", "rahat"],
                "season": "year_round",
                "frequency_weight": 1.0
            }
        }


class MealSelectionRequest(BaseModel):
    """Request: User selects a meal"""
    meal_id: str
    country_code: str  # e.g., "japan", "turkey"
    quantity: Optional[int] = 1


class MealSifatGuessRequest(BaseModel):
    """Request: User guesses personality match"""
    meal_id: str
    guess: Literal["yes", "no", "unsure"]  # Does this fit my personality?


class MealSelection(BaseModel):
    """
    Stored meal selection document (MongoDB).

    Used for:
    - Weekly leaderboard tracking
    - User's meal history
    - Sıfat learning
    """
    _id: Optional[str] = None  # MongoDB _id
    user_id: int
    meal_id: str
    meal_name_en: str
    country_code: str
    selected_at: datetime
    sifat_guess: Optional[str] = None  # "yes", "no", "unsure"
    sifat_correct: Optional[bool] = None  # True if guess was right
    coins_earned: int  # 10 for selection, +5 if guess correct


class MealLeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: int
    username: str
    avatar: Optional[str] = None
    meals_completed: int
    coins_earned: int
    accuracy_percent: Optional[float] = None  # sifat guesses correct %
    streak_days: Optional[int] = None


# ── Country mapping ────────────────────────────────────────────────────

COUNTRY_CODES = {
    "japan": "ja",
    "turkey": "tr",
    "china": "zh",
    "india": "india",
    "italy": "italy",
    "greece": "greece",
    "germany": "germany",
    "france": "france",
    "korea": "ko",
    "portugal": "pt",
    "bangladesh": "bn",
    "indonesia": "id",
    "pakistan": "ur",
    "thailand": "th",
    "malaysia": "malaysia",
    "mexico": "mexico",
    "vietnam": "vi",
    "philippines": "tl",
}

# Rotation: Week 1 = Japan, Week 2 = Turkey, etc.
WEEK_ROTATION = [
    "japan",
    "turkey",
    "china",
    "india",
    "italy",
    "greece",
    "germany",
    "france",
    "korea",
    "portugal",
    "bangladesh",
    "indonesia",
    "pakistan",
    "thailand",
    "malaysia",
    "mexico",
    "vietnam",
    "philippines",
]
