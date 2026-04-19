"""
models.py
=========
Pydantic veri modelleri - Beslenme koçluğu için type hints ve validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ── Yemek Modelleri ─────────────────────────────────────────────────────────

class DietaryPreferences(BaseModel):
    """Beslenme tercihler modeli"""
    omnivore: bool = True
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False

    class Config:
        description = "Kullanıcının beslenme tercihleri"


class Nutrition(BaseModel):
    """Beslenme bilgileri"""
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

    class Config:
        description = "Makro nutrient bilgileri"


class Meal(BaseModel):
    """Tek bir yemek"""
    id: str = Field(..., description="Benzersiz yemek ID (tr_breakfast_001)")
    name_tr: str = Field(..., description="Türkçe adı")
    name_en: str = Field(..., description="İngilizce adı")
    description: Optional[str] = None
    nutrition: Nutrition
    prep_time_min: int = Field(..., description="Hazırlık süresi dakika")
    dietary: DietaryPreferences
    vegan_substitute: Optional[str] = Field(None, description="Vegan alternatifi")
    sifat_appeal: List[str] = Field(default_factory=list, description="Çekici sıfatlar")
    season: str = Field(default="year_round", description="Mevsim (year_round, summer, winter, spring, autumn)")
    frequency_weight: float = Field(default=1.0, description="Önerilme sıklığı ağırlığı")

    class Config:
        description = "Yemek modeli"


class MealsByType(BaseModel):
    """Öğün tipine göre yemekler"""
    breakfast: List[Meal]
    lunch: List[Meal]
    dinner: List[Meal]

    class Config:
        description = "Sabah, öğlen, akşam yemekleri"


class CountryMeals(BaseModel):
    """Bir ülkenin tüm yemekleri"""
    country: str
    language_code: str = Field(..., description="ISO 639-1 dil kodu (tr, en, hi, etc.)")
    meals: MealsByType

    class Config:
        description = "Ülkeye özgü yemek havuzu"


# ── Sıfat Mapping Modelleri ─────────────────────────────────────────────────

class MealPreferences(BaseModel):
    """Bir sıfat grubu için yemek tercihleri"""
    breakfast: List[str] = Field(..., description="Sabah yemek özellikleri")
    lunch: List[str] = Field(..., description="Öğlen yemek özellikleri")
    dinner: List[str] = Field(..., description="Akşam yemek özellikleri")

    class Config:
        description = "Öğün tipine göre yemek tercihleri"


class SifatPreferences(BaseModel):
    """Sıfat-yemek mapping"""
    weight: float = Field(..., description="Sıfat ağırlığı (1.0-2.0)")
    preferences: MealPreferences

    class Config:
        description = "Bir sıfat için yemek tercihleri"


class SifatMapping(BaseModel):
    """Tüm sıfat-yemek mappings"""
    sifat_meal_preferences: Dict[str, SifatPreferences]

    class Config:
        description = "Sıfat → Yemek tercihleri mapping"


# ── Kullanıcı Profili Modelleri ────────────────────────────────────────────

class UserSifat(BaseModel):
    """Kullanıcının bir sıfatı"""
    sifat: str
    score: float = Field(..., ge=0.0, le=1.0, description="Sıfat skoru (0-1)")

    class Config:
        description = "Kullanıcının sıfat skoru"


class UserMealHistory(BaseModel):
    """Kullanıcının yemek geçmişi"""
    meal_id: str
    date: str = Field(..., description="YYYY-MM-DD formatı")
    meal_type: str = Field(..., description="breakfast, lunch, dinner")
    feedback: Optional[str] = None  # "liked", "disliked", "neutral"

    class Config:
        description = "Önceki yemek kaydı"


class UserProfile(BaseModel):
    """Tavsiye için kullanıcı profili"""
    user_id: int
    country: str = Field(default="Turkey", description="Ülke adı")
    language_code: str = Field(default="tr", description="Dil kodu")
    sifats: List[UserSifat]
    dietary_preference: DietaryPreferences = Field(default_factory=DietaryPreferences)
    last_7_meals: List[UserMealHistory] = Field(default_factory=list)

    class Config:
        description = "Beslenme tavsiyesi için kullanıcı profili"


# ── Tavsiye Output Modelleri ───────────────────────────────────────────────

class MealRecommendation(BaseModel):
    """Tek bir öğün tavsiyesi"""
    name: str
    description: Optional[str] = None
    reason: str = Field(..., description="Neden bu öğün tavsiye ediliyor")
    nutrition: Optional[Nutrition] = None
    prep_time_min: Optional[int] = None
    vegan_substitute: Optional[str] = None

    class Config:
        description = "Tek öğün tavsiyesi"


class DailyRecommendation(BaseModel):
    """Günlük tavsiye"""
    date: str = Field(..., description="YYYY-MM-DD formatı")
    breakfast: MealRecommendation
    lunch: MealRecommendation
    dinner: MealRecommendation
    user_sifats: List[str] = Field(description="Kullanıcının en güçlü sıfatları")

    class Config:
        description = "Günlük 3 öğün tavsiyesi"


class FeedbackRequest(BaseModel):
    """Kullanıcı feedback kaydı"""
    user_id: int
    meal_id: str
    date: str
    meal_type: str
    feedback: str = Field(..., description="'liked', 'disliked', 'neutral'")

    class Config:
        description = "Yemek hakkında kullanıcı geri bildirimi"


# ── Helper Modelleri ────────────────────────────────────────────────────────

class CountryInfo(BaseModel):
    """Ülke bilgisi"""
    name: str
    language_code: str
    meal_count: int = 0

    class Config:
        description = "Ülke bilgisi"
