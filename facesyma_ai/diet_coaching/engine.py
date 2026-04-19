"""
engine.py
=========
Beslenme tavsiye motoru - Ana algoritma
"""

import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from .models import (
    UserProfile,
    UserSifat,
    DailyRecommendation,
    MealRecommendation,
    Meal,
    DietaryPreferences,
)
from .database import get_database

log = logging.getLogger(__name__)


class RecommendationEngine:
    """Tavsiye motoru - Sıfatlara göre yemek önerileri"""

    def __init__(self):
        self.db = get_database()

    def _calculate_meal_score(
        self,
        meal: Meal,
        user_sifats: List[UserSifat],
        meal_type: str,
    ) -> float:
        """
        Bir yemek için kullanıcıya ait skor hesapla.

        Sıfat match ağırlıkları: sıfat ağırlığı × sıfat skoru
        """
        total_score = 0.0

        for user_sifat in user_sifats:
            sifat_name = user_sifat.sifat
            sifat_score = user_sifat.score

            # Sıfatın yemek tavsiyesinde mi var kontrol et
            if sifat_name not in meal.sifat_appeal:
                continue

            # Sıfatın ağırlığını al
            sifat_weight = self.db.get_sifat_weight(sifat_name)

            # Puan hesapla: weight × user score
            score_contribution = sifat_weight * sifat_score
            total_score += score_contribution

        # Yemek frequency weight'ini de ekle (nadir yemekler boost)
        total_score *= meal.frequency_weight

        return total_score

    def _filter_meals_by_dietary(
        self,
        meals: List[Meal],
        dietary_pref: DietaryPreferences,
    ) -> List[Meal]:
        """
        Beslenme tercihlerine göre yemekleri filtrele.

        Vegan istenirse: Sadece vegan yemekleri döndür.
        Vegetarian istenirse: Vegetarian ve vegan yemekleri döndür.
        Gluten-free istenirse: Sadece gluten-free döndür.
        """
        filtered = []

        for meal in meals:
            # Gluten-free kontrol
            if dietary_pref.gluten_free and not meal.dietary.gluten_free:
                continue

            # Vegan kontrol
            if dietary_pref.vegan and not meal.dietary.vegan:
                continue

            # Vegetarian kontrol
            if dietary_pref.vegetarian and not meal.dietary.vegetarian:
                continue

            # Omnivore kontrol (her şey)
            if (
                not dietary_pref.omnivore
                and not dietary_pref.vegetarian
                and not dietary_pref.vegan
            ):
                # Hiçbir tercih belirtilmemişse omnivore yemeklere izin ver
                pass

            filtered.append(meal)

        return filtered

    def _exclude_recent_meals(
        self,
        meals: List[Meal],
        recent_meal_ids: List[str],
    ) -> List[Meal]:
        """
        Son 7 gündeki yemekleri hariç tut (tekrarlama engelle).
        """
        return [meal for meal in meals if meal.id not in recent_meal_ids]

    def _get_top_meals(
        self,
        meals: List[Meal],
        user_sifats: List[UserSifat],
        meal_type: str,
        count: int = 5,
    ) -> List[Tuple[Meal, float]]:
        """
        Top N yemeği skor ile döndür.

        Returns: [(Meal, score), ...]
        """
        # Her yemek için skoru hesapla
        scored_meals = [
            (meal, self._calculate_meal_score(meal, user_sifats, meal_type))
            for meal in meals
        ]

        # Skora göre sırala
        scored_meals.sort(key=lambda x: x[1], reverse=True)

        return scored_meals[:count]

    def get_daily_recommendation(
        self,
        user_profile: UserProfile,
    ) -> DailyRecommendation:
        """
        Kullanıcı profili için günlük tavsiye yap.

        Adımlar:
        1. Yemekleri beslenme tercihine göre filtrele
        2. Son 7 gündeki yemekleri hariç tut
        3. Her öğün için en iyi yemekleri seç
        """
        lang_code = user_profile.language_code
        country = self.db.get_country_meals(lang_code)

        if not country:
            raise ValueError(f"Country not found: {lang_code}")

        # Son 7 gündeki yemek ID'lerini al
        recent_meal_ids = [meal.meal_id for meal in user_profile.last_7_meals]

        # Beslenme tercihini al (opsiyonel)
        dietary_pref = user_profile.dietary_preference

        # Sabah, öğlen, akşam için tavsiye yap
        breakfast_meals = country.meals.breakfast
        breakfast_meals = self._filter_meals_by_dietary(breakfast_meals, dietary_pref)
        breakfast_meals = self._exclude_recent_meals(breakfast_meals, recent_meal_ids)
        breakfast_top = self._get_top_meals(breakfast_meals, user_profile.sifats, "breakfast", count=1)

        lunch_meals = country.meals.lunch
        lunch_meals = self._filter_meals_by_dietary(lunch_meals, dietary_pref)
        lunch_meals = self._exclude_recent_meals(lunch_meals, recent_meal_ids)
        lunch_top = self._get_top_meals(lunch_meals, user_profile.sifats, "lunch", count=1)

        dinner_meals = country.meals.dinner
        dinner_meals = self._filter_meals_by_dietary(dinner_meals, dietary_pref)
        dinner_meals = self._exclude_recent_meals(dinner_meals, recent_meal_ids)
        dinner_top = self._get_top_meals(dinner_meals, user_profile.sifats, "dinner", count=1)

        # Fallback: Eğer yemek bulunamadısa default seç
        if not breakfast_top:
            breakfast_top = [(breakfast_meals[0], 0) if breakfast_meals else (None, 0)]
        if not lunch_top:
            lunch_top = [(lunch_meals[0], 0) if lunch_meals else (None, 0)]
        if not dinner_top:
            dinner_top = [(dinner_meals[0], 0) if dinner_meals else (None, 0)]

        breakfast_meal = breakfast_top[0][0]
        lunch_meal = lunch_top[0][0]
        dinner_meal = dinner_top[0][0]

        # MealRecommendation oluştur
        breakfast_rec = MealRecommendation(
            name=breakfast_meal.name_tr,
            description=breakfast_meal.description,
            reason=self._generate_reason(breakfast_meal, user_profile.sifats),
            nutrition=breakfast_meal.nutrition,
            prep_time_min=breakfast_meal.prep_time_min,
            vegan_substitute=breakfast_meal.vegan_substitute,
        )

        lunch_rec = MealRecommendation(
            name=lunch_meal.name_tr,
            description=lunch_meal.description,
            reason=self._generate_reason(lunch_meal, user_profile.sifats),
            nutrition=lunch_meal.nutrition,
            prep_time_min=lunch_meal.prep_time_min,
            vegan_substitute=lunch_meal.vegan_substitute,
        )

        dinner_rec = MealRecommendation(
            name=dinner_meal.name_tr,
            description=dinner_meal.description,
            reason=self._generate_reason(dinner_meal, user_profile.sifats),
            nutrition=dinner_meal.nutrition,
            prep_time_min=dinner_meal.prep_time_min,
            vegan_substitute=dinner_meal.vegan_substitute,
        )

        # Top sıfatları bul
        top_sifats = sorted(user_profile.sifats, key=lambda x: x.score, reverse=True)[:3]
        top_sifat_names = [s.sifat for s in top_sifats]

        return DailyRecommendation(
            date=datetime.now().strftime("%Y-%m-%d"),
            breakfast=breakfast_rec,
            lunch=lunch_rec,
            dinner=dinner_rec,
            user_sifats=top_sifat_names,
        )

    def _generate_reason(
        self,
        meal: Meal,
        user_sifats: List[UserSifat],
    ) -> str:
        """
        Yemek neden tavsiye ediliyor açıkla.
        """
        matching_sifats = []
        for user_sifat in user_sifats:
            if user_sifat.sifat in meal.sifat_appeal:
                matching_sifats.append(user_sifat.sifat)

        if matching_sifats:
            sifat_str = ", ".join(matching_sifats[:2])
            return f"Sıfatlarınız ({sifat_str}) için ideal bir seçim"
        return "Çeşitlilik ve beslenme açısından iyi bir seçim"

    def get_alternatives(
        self,
        user_profile: UserProfile,
        meal_type: str,
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Bir öğün için alternatif tavsiyeleri al.
        """
        lang_code = user_profile.language_code
        country = self.db.get_country_meals(lang_code)

        if not country:
            return []

        # Beslenme tercihini kontrol et
        dietary_pref = user_profile.dietary_preference
        recent_meal_ids = [meal.meal_id for meal in user_profile.last_7_meals]

        # Öğün tipine göre yemekleri al
        if meal_type == "breakfast":
            meals = country.meals.breakfast
        elif meal_type == "lunch":
            meals = country.meals.lunch
        else:
            meals = country.meals.dinner

        # Filtrele ve tekrarlama engelle
        meals = self._filter_meals_by_dietary(meals, dietary_pref)
        meals = self._exclude_recent_meals(meals, recent_meal_ids)

        # Top yemekleri al
        top_meals = self._get_top_meals(meals, user_profile.sifats, meal_type, count=count)

        # Dict olarak döndür
        alternatives = []
        for meal, score in top_meals:
            alternatives.append({
                "name": meal.name_tr,
                "description": meal.description,
                "reason": self._generate_reason(meal, user_profile.sifats),
                "score": round(score, 2),
            })

        return alternatives


# Global engine singleton
_engine: Optional[RecommendationEngine] = None


def get_engine() -> RecommendationEngine:
    """Global tavsiye motorunu al"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine


# ── Public Functions ────────────────────────────────────────────────────────

def get_daily_recommendation(user_profile: UserProfile) -> DailyRecommendation:
    """Günlük tavsiye al"""
    engine = get_engine()
    return engine.get_daily_recommendation(user_profile)


def get_meal_suggestions(
    user_profile: UserProfile,
    meal_type: str,
    count: int = 3,
) -> List[Dict[str, Any]]:
    """Bir öğün için alternatif tavsiyeleri al"""
    engine = get_engine()
    return engine.get_alternatives(user_profile, meal_type, count)


def record_meal_feedback(
    user_id: int,
    meal_id: str,
    feedback: str,
) -> bool:
    """
    Kullanıcının yemek feedback'ini kaydet.
    (Bu fonksiyon ileriye yönelik - şu an boş)
    """
    log.info(f"Recorded feedback: user={user_id}, meal={meal_id}, feedback={feedback}")
    return True
