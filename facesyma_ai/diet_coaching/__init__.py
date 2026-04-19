"""
facesyma_ai/diet_coaching/
===========================
Gündelik Beslenme Koçluğu Modülü

Her kullanıcının sıfatlarına, ülke/kültürüne ve beslenme tercihlerine göre
gündelik 3 öğün (sabah-öğlen-akşam) yemek önerileri sunar.

Özellikler:
  - 201 sıfata göre kişiselleştirilmiş öneriler
  - 18 ülkenin yerel mutfak yemekleri
  - Vegetarian/Vegan/Gluten-free destek (opsiyonel)
  - 7 günlük cycle: Aynı yemek 1 hafta sonra tekrar
  - Kalori & beslenme bilgisi

Kullanım:
    from facesyma_ai.diet_coaching import get_daily_recommendation

    recommendation = get_daily_recommendation(
        user_id=123,
        country="Turkey",
        sifats=[("disiplinli", 0.85), ("saglik_bilinc", 0.78)],
        vegetarian=False,
        vegan=False,
        gluten_free=False
    )
"""

__version__ = "1.0.0"
__author__ = "Facesyma AI Team"

from .engine import (
    get_daily_recommendation,
    get_meal_suggestions,
    record_meal_feedback,
)
from .database import (
    load_meals_for_country,
    get_all_countries,
    get_country_meals,
)

__all__ = [
    "get_daily_recommendation",
    "get_meal_suggestions",
    "record_meal_feedback",
    "load_meals_for_country",
    "get_all_countries",
    "get_country_meals",
]
