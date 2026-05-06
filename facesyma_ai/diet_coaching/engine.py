"""
engine.py
=========
Beslenme tavsiye motoru - Ana algoritma
"""

import logging
from datetime import datetime
from operator import itemgetter, attrgetter
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

# 18 dil için tavsiye gerekçesi şablonları
_REASON_TMPL: Dict[str, Tuple[str, str]] = {
    # (eşleşme varsa, yoksa)
    "tr": ("Sıfatlarınız ({}) için ideal bir seçim",      "Çeşitlilik ve beslenme açısından iyi bir seçim"),
    "en": ("An ideal pick for your traits ({})",           "A great choice for variety and balanced nutrition"),
    "de": ("Ideal für Ihre Eigenschaften ({})",            "Gute Wahl für Abwechslung und ausgewogene Ernährung"),
    "ru": ("Идеально подходит для ваших качеств ({})",     "Отличный выбор для разнообразия и баланса"),
    "ar": ("خيار مثالي لصفاتك ({})",                       "خيار جيد للتنوع والتغذية المتوازنة"),
    "es": ("Una elección ideal para tus rasgos ({})",      "Buena opción para variedad y nutrición equilibrada"),
    "ko": ("당신의 특성({})에 이상적인 선택",                  "다양성과 균형 잡힌 영양을 위한 선택"),
    "ja": ("あなたの特性（{}）に最適な選択",                   "バランスの取れた栄養のための良い選択"),
    "zh": ("最适合您特质（{}）的选择",                         "有助于饮食多样化和均衡营养的选择"),
    "hi": ("आपके गुणों ({}) के लिए आदर्श विकल्प",          "विविधता और संतुलित पोषण के लिए अच्छा विकल्प"),
    "fr": ("Un choix idéal pour vos traits ({})",          "Un bon choix pour la variété et la nutrition équilibrée"),
    "pt": ("Escolha ideal para suas características ({})", "Boa escolha para variedade e nutrição equilibrada"),
    "bn": ("আপনার বৈশিষ্ট্যের ({}) জন্য আদর্শ পছন্দ",     "বৈচিত্র্য ও সুষম পুষ্টির জন্য ভালো পছন্দ"),
    "id": ("Pilihan ideal untuk sifat Anda ({})",          "Pilihan bagus untuk variasi dan nutrisi seimbang"),
    "ur": ("آپ کی خصوصیات ({}) کے لیے بہترین انتخاب",     "تنوع اور متوازن غذائیت کے لیے اچھا انتخاب"),
    "it": ("Scelta ideale per i tuoi tratti ({})",         "Buona scelta per varietà e nutrizione equilibrata"),
    "vi": ("Lựa chọn lý tưởng cho đặc điểm của bạn ({})", "Lựa chọn tốt cho sự đa dạng và dinh dưỡng cân bằng"),
    "pl": ("Idealny wybór dla Twoich cech ({})",           "Dobry wybór dla różnorodności i zbilansowanego odżywiania"),
}


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
        _dp_gf   = dietary_pref.gluten_free
        _dp_veg  = dietary_pref.vegan
        _dp_vegr = dietary_pref.vegetarian
        _dp_omni = dietary_pref.omnivore

        for meal in meals:
            _md = meal.dietary
            # Gluten-free kontrol
            if _dp_gf and not _md.gluten_free:
                continue

            # Vegan kontrol
            if _dp_veg and not _md.vegan:
                continue

            # Vegetarian kontrol
            if _dp_vegr and not _md.vegetarian:
                continue

            # Omnivore kontrol (her şey)
            if not _dp_omni and not _dp_vegr and not _dp_veg:
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
        scored_meals.sort(key=itemgetter(1), reverse=True)

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
        _filter  = self._filter_meals_by_dietary
        _exclude = self._exclude_recent_meals
        _top     = self._get_top_meals
        _reason  = self._generate_reason
        _lang    = user_profile.language_code or "en"
        country_code = user_profile.country_code
        country = self.db.get_country_meals(country_code)

        if not country:
            raise ValueError(f"Country not found: {country_code}")

        # Son 7 gündeki yemek ID'lerini al
        recent_meal_ids = [meal.meal_id for meal in user_profile.last_7_meals]

        # Beslenme tercihini al (opsiyonel)
        dietary_pref = user_profile.dietary_preference

        # Sabah, öğlen, akşam için tavsiye yap
        _sifats = user_profile.sifats
        _cm = country.meals

        def _best_meals(raw: list, label: str, count: int = 3):
            filtered = _filter(_exclude(raw, recent_meal_ids), dietary_pref)
            if not filtered:
                filtered = _exclude(raw, recent_meal_ids) or raw
            top = _top(filtered, _sifats, label, count=count)
            return top if top else [(filtered[0], 0)] if filtered else [(None, 0)]

        def _to_recs(top) -> List[MealRecommendation]:
            return [
                MealRecommendation(
                    name=meal.name_tr,
                    description=meal.description,
                    reason=_reason(meal, _sifats, _lang),
                    nutrition=meal.nutrition,
                    prep_time_min=meal.prep_time_min,
                    vegan_substitute=meal.vegan_substitute,
                )
                for meal, _ in top
                if meal is not None
            ]

        breakfast_recs = _to_recs(_best_meals(_cm.breakfast, "breakfast"))
        lunch_recs     = _to_recs(_best_meals(_cm.lunch,     "lunch"))
        dinner_recs    = _to_recs(_best_meals(_cm.dinner,    "dinner"))

        if not breakfast_recs or not lunch_recs or not dinner_recs:
            raise ValueError("No meals available for recommendation.")

        top_sifats = sorted(_sifats, key=attrgetter('score'), reverse=True)[:3]

        return DailyRecommendation(
            date=datetime.now().strftime("%Y-%m-%d"),
            breakfast=breakfast_recs,
            lunch=lunch_recs,
            dinner=dinner_recs,
            user_sifats=[s.sifat for s in top_sifats],
        )

    def _generate_reason(
        self,
        meal: Meal,
        user_sifats: List[UserSifat],
        language_code: str = "en",
    ) -> str:
        """
        Yemek neden tavsiye ediliyor — kullanıcı dilinde açıkla.
        """
        tmpl_match, tmpl_fallback = _REASON_TMPL.get(
            language_code, _REASON_TMPL["en"]
        )
        matching_sifats = [
            us.sifat for us in user_sifats if us.sifat in meal.sifat_appeal
        ]
        if matching_sifats:
            return tmpl_match.format(", ".join(matching_sifats[:2]))
        return tmpl_fallback

    def get_alternatives(
        self,
        user_profile: UserProfile,
        meal_type: str,
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Bir öğün için alternatif tavsiyeleri al.
        """
        country_code = user_profile.country_code
        country = self.db.get_country_meals(country_code)

        if not country:
            return []

        dietary_pref = user_profile.dietary_preference
        recent_meal_ids = [meal.meal_id for meal in user_profile.last_7_meals]

        _cm = country.meals
        if meal_type == "breakfast":
            meals = _cm.breakfast
        elif meal_type == "lunch":
            meals = _cm.lunch
        else:
            meals = _cm.dinner

        meals = self._filter_meals_by_dietary(meals, dietary_pref)
        meals = self._exclude_recent_meals(meals, recent_meal_ids)

        _sifats = user_profile.sifats
        _lang   = user_profile.language_code or "en"
        top_meals = self._get_top_meals(meals, _sifats, meal_type, count=count)

        # Dict olarak döndür
        alternatives = []
        for meal, score in top_meals:
            alternatives.append({
                "name": meal.name_tr,
                "description": meal.description,
                "reason": self._generate_reason(meal, _sifats, _lang),
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
