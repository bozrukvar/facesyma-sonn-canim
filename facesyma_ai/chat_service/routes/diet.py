"""
routes/diet.py
==============
Beslenme Koçluğu API Endpoints

Endpoints:
  POST   /api/v1/diet/recommendation/   → Günlük tavsiye al
  GET    /api/v1/diet/alternatives/     → Alternatif tavsiyeleri al
  POST   /api/v1/diet/feedback/         → Feedback kaydet
  GET    /api/v1/diet/countries/        → Ülkeleri listele
  GET    /api/v1/diet/meals/            → Yemekleri getir
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from facesyma_ai.diet_coaching import (
    get_daily_recommendation,
    get_meal_suggestions,
    record_meal_feedback,
)
from facesyma_ai.diet_coaching.database import get_database
from facesyma_ai.diet_coaching.models import (
    UserProfile,
    UserSifat,
    DietaryPreferences,
    DailyRecommendation,
)
from facesyma_ai.diet_coaching.utils import (
    format_recommendation_for_chat,
    calculate_daily_nutrition,
    format_nutrition_info,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diet", tags=["diet_coaching"])


# ── Request Models ─────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    """Tavsiye isteği"""
    user_id: int
    country: str = Field(default="Turkey", description="Ülke adı")
    language_code: str = Field(default="tr", description="Dil kodu")
    sifats: List[dict] = Field(..., description="[{sifat: str, score: float}, ...]")
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False


class AlternativesRequest(BaseModel):
    """Alternatif tavsiyeleri isteği"""
    user_id: int
    country: str = Field(default="Turkey")
    language_code: str = Field(default="tr")
    sifats: List[dict]
    meal_type: str = Field(..., description="breakfast, lunch, dinner")
    count: int = Field(default=3, ge=1, le=5)
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False


class FeedbackRequest(BaseModel):
    """Feedback isteği"""
    user_id: int
    meal_id: str
    date: str
    meal_type: str
    feedback: str = Field(..., description="'liked', 'disliked', 'neutral'")


# ── Response Models ────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    """Tavsiye cevabı"""
    status: str = "success"
    data: DailyRecommendation
    nutrition: Optional[dict] = None
    explanation: Optional[str] = None


class AlternativesResponse(BaseModel):
    """Alternatif tavsiyeleri cevabı"""
    status: str = "success"
    meal_type: str
    alternatives: List[dict]
    count: int


class CountriesResponse(BaseModel):
    """Ülkeler listesi cevabı"""
    status: str = "success"
    countries: List[dict]
    count: int


class MealsResponse(BaseModel):
    """Yemekler cevabı"""
    status: str = "success"
    country: str
    meal_type: str
    meals: List[dict]
    count: int


# ── API Endpoints ──────────────────────────────────────────────────────────

@router.post("/recommendation/", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """
    Günlük tavsiye al.

    Kullanıcının sıfatlarına, ülke/kültürüne ve beslenme tercihlerine göre
    sabah-öğlen-akşam yemek önerileri sunar.
    """
    try:
        # UserProfile oluştur
        user_sifats = [
            UserSifat(sifat=s["sifat"], score=s["score"])
            for s in request.sifats
        ]

        dietary_pref = DietaryPreferences(
            omnivore=not request.vegetarian and not request.vegan,
            vegetarian=request.vegetarian,
            vegan=request.vegan,
            gluten_free=request.gluten_free,
        )

        user_profile = UserProfile(
            user_id=request.user_id,
            country=request.country,
            language_code=request.language_code,
            sifats=user_sifats,
            dietary_preference=dietary_pref,
        )

        # Tavsiye al
        recommendation = get_daily_recommendation(user_profile)

        # Beslenme bilgilerini hesapla
        meals_list = [
            recommendation.breakfast.dict(),
            recommendation.lunch.dict(),
            recommendation.dinner.dict(),
        ]
        nutrition = calculate_daily_nutrition(meals_list)

        return RecommendationResponse(
            status="success",
            data=recommendation,
            nutrition=nutrition,
            explanation=format_recommendation_for_chat(
                recommendation.dict(), request.language_code
            ),
        )

    except ValueError as e:
        log.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Tavsiye alınamadı")


@router.post("/alternatives/", response_model=AlternativesResponse)
async def get_alternatives(request: AlternativesRequest):
    """
    Bir öğün için alternatif tavsiyeleri al.

    Aynı öğün tipi için farklı yemek seçenekleri sunar.
    """
    try:
        # UserProfile oluştur
        user_sifats = [
            UserSifat(sifat=s["sifat"], score=s["score"])
            for s in request.sifats
        ]

        dietary_pref = DietaryPreferences(
            omnivore=not request.vegetarian and not request.vegan,
            vegetarian=request.vegetarian,
            vegan=request.vegan,
            gluten_free=request.gluten_free,
        )

        user_profile = UserProfile(
            user_id=request.user_id,
            country=request.country,
            language_code=request.language_code,
            sifats=user_sifats,
            dietary_preference=dietary_pref,
        )

        # Alternatifler al
        alternatives = get_meal_suggestions(
            user_profile, request.meal_type, request.count
        )

        return AlternativesResponse(
            status="success",
            meal_type=request.meal_type,
            alternatives=alternatives,
            count=len(alternatives),
        )

    except Exception as e:
        log.error(f"Alternatives error: {e}")
        raise HTTPException(status_code=500, detail="Alternatifler alınamadı")


@router.post("/feedback/")
async def submit_feedback(request: FeedbackRequest):
    """
    Yemek hakkında feedback kaydet.

    Kullanıcının feedback'i kaydedilir ve
    gelecekteki tavsiyeler bu bilgi kullanılarak kişiselleştirilir.
    """
    try:
        feedback_valid = request.feedback.lower() in ["liked", "disliked", "neutral"]
        if not feedback_valid:
            raise ValueError("Feedback must be 'liked', 'disliked', or 'neutral'")

        # Feedback kaydet
        success = record_meal_feedback(
            request.user_id,
            request.meal_id,
            request.feedback,
        )

        if not success:
            raise Exception("Feedback could not be recorded")

        log.info(
            f"Feedback recorded: user={request.user_id}, "
            f"meal={request.meal_id}, feedback={request.feedback}"
        )

        return {
            "status": "success",
            "message": f"Feedback başarıyla kaydedildi: {request.feedback}",
        }

    except ValueError as e:
        log.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail="Feedback kaydedilemedi")


@router.get("/countries/", response_model=CountriesResponse)
async def list_countries():
    """
    Mevcut ülkelerin listesini al.

    Sistem tarafından desteklenen ülkeleri ve her ülkeye ait yemek sayısını döndür.
    """
    try:
        db = get_database()
        countries = db.get_available_countries()

        return CountriesResponse(
            status="success",
            countries=countries,
            count=len(countries),
        )

    except Exception as e:
        log.error(f"Countries error: {e}")
        raise HTTPException(status_code=500, detail="Ülkeler alınamadı")


@router.get("/meals/", response_model=MealsResponse)
async def get_meals(
    country: str = Query("Turkey", description="Ülke adı"),
    language_code: str = Query("tr", description="Dil kodu"),
    meal_type: Optional[str] = Query(None, description="breakfast, lunch, dinner"),
):
    """
    Bir ülkeye ait yemekleri al.

    Opsiyonel olarak öğün tipine göre filtreleyebilirsiniz.
    """
    try:
        db = get_database()
        country_data = db.get_country_meals(language_code)

        if not country_data:
            raise ValueError(f"Country not found: {language_code}")

        # Öğün tipine göre filtrele
        if meal_type:
            if meal_type not in ["breakfast", "lunch", "dinner"]:
                raise ValueError("meal_type must be 'breakfast', 'lunch', or 'dinner'")

            meals = db.get_meals_by_type(language_code, meal_type)
            meals_list = [meal.dict() for meal in meals]
        else:
            # Tüm yemekleri döndür
            meals_list = []
            for mt in ["breakfast", "lunch", "dinner"]:
                meals = db.get_meals_by_type(language_code, mt)
                meals_list.extend([meal.dict() for meal in meals])
            meal_type = "all"

        return MealsResponse(
            status="success",
            country=country,
            meal_type=meal_type,
            meals=meals_list,
            count=len(meals_list),
        )

    except ValueError as e:
        log.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Meals error: {e}")
        raise HTTPException(status_code=500, detail="Yemekler alınamadı")


@router.get("/health/")
async def health_check():
    """Beslenme koçluğu modülü sağlık kontrolü"""
    try:
        db = get_database()
        countries = db.get_available_countries()

        return {
            "status": "healthy",
            "module": "diet_coaching",
            "countries_loaded": len(countries),
            "countries": [c["name"] for c in countries],
        }

    except Exception as e:
        log.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Beslenme koçluğu modülü kullanılamıyor",
        )
