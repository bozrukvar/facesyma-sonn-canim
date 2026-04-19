"""
utils.py
========
Yardımcı fonksiyonlar - Veri dönüşümleri, validation
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


def get_user_sifat_scores(sifat_data: Dict) -> List[Tuple[str, float]]:
    """
    Kullanıcının sıfat skorlarını formatlı liste olarak döndür.

    Input: {sifat_name: score, ...}
    Output: [(sifat_name, score), ...]
    """
    if not sifat_data:
        return []

    sifats = [
        (sifat_name, score)
        for sifat_name, score in sifat_data.items()
        if isinstance(score, (int, float)) and 0 <= score <= 1
    ]

    # Skora göre sırala
    sifats.sort(key=lambda x: x[1], reverse=True)

    return sifats


def validate_dietary_preferences(
    vegan: bool = False,
    vegetarian: bool = False,
    gluten_free: bool = False,
) -> Dict[str, bool]:
    """
    Beslenme tercihlerini doğrula ve normalize et.

    Kurallar:
    - Vegan ise, vegetarian otomatikman True
    - Hiçbir tercih seçilmemişse, omnivore True
    """
    # Vegan ise vegetarian'da True olmalı
    if vegan:
        vegetarian = True

    return {
        "omnivore": not vegan and not vegetarian,
        "vegetarian": vegetarian,
        "vegan": vegan,
        "gluten_free": gluten_free,
    }


def get_last_n_days_meals(
    meal_history: List[Dict],
    days: int = 7,
) -> List[Dict]:
    """
    Son N gündeki yemekleri döndür.

    meal_history: [{"meal_id": ..., "date": "2026-04-19", ...}]
    """
    today = datetime.now()
    cutoff_date = today - timedelta(days=days)

    recent_meals = []
    for meal in meal_history:
        try:
            meal_date = datetime.strptime(meal["date"], "%Y-%m-%d")
            if meal_date >= cutoff_date:
                recent_meals.append(meal)
        except (KeyError, ValueError) as e:
            log.warning(f"Invalid meal history entry: {e}")

    return recent_meals


def format_recommendation_for_chat(
    recommendation: Dict,
    language: str = "tr",
) -> str:
    """
    Tavsiyeyi chat formatında döndür.

    language: "tr" (Türkçe), "en" (İngilizce)
    """
    if language == "tr":
        return _format_recommendation_tr(recommendation)
    else:
        return _format_recommendation_en(recommendation)


def _format_recommendation_tr(recommendation: Dict) -> str:
    """Türkçe format"""
    date = recommendation.get("date", "Bugün")
    user_sifats = recommendation.get("user_sifats", [])
    sifat_str = ", ".join(user_sifats) if user_sifats else "profil verileriniz"

    breakfast = recommendation.get("breakfast", {})
    lunch = recommendation.get("lunch", {})
    dinner = recommendation.get("dinner", {})

    text = f"""
🍽️ **{date} Beslenme Koçluğu**

Sıfatlarınız: {sifat_str}

**☀️ Sabah Öğünü:**
🥣 {breakfast.get('name', 'N/A')}
📝 {breakfast.get('reason', 'İyi bir seçim')}

**🌤️ Öğlen Öğünü:**
🥗 {lunch.get('name', 'N/A')}
📝 {lunch.get('reason', 'İyi bir seçim')}

**🌙 Akşam Öğünü:**
🍲 {dinner.get('name', 'N/A')}
📝 {dinner.get('reason', 'İyi bir seçim')}

💡 *Alternatif tavsiyeleri görmek için "başka seçenekler" yazabilirsiniz*
"""
    return text.strip()


def _format_recommendation_en(recommendation: Dict) -> str:
    """İngilizce format"""
    date = recommendation.get("date", "Today")
    user_sifats = recommendation.get("user_sifats", [])
    sifat_str = ", ".join(user_sifats) if user_sifats else "your profile"

    breakfast = recommendation.get("breakfast", {})
    lunch = recommendation.get("lunch", {})
    dinner = recommendation.get("dinner", {})

    text = f"""
🍽️ **{date} Meal Recommendations**

Your traits: {sifat_str}

**☀️ Breakfast:**
🥣 {breakfast.get('name', 'N/A')}
📝 {breakfast.get('reason', 'A great choice')}

**🌤️ Lunch:**
🥗 {lunch.get('name', 'N/A')}
📝 {lunch.get('reason', 'A great choice')}

**🌙 Dinner:**
🍲 {dinner.get('name', 'N/A')}
📝 {dinner.get('reason', 'A great choice')}

💡 *Type "other options" to see alternatives*
"""
    return text.strip()


def calculate_daily_nutrition(meals: List[Dict]) -> Dict:
    """
    Günlük toplam beslenme bilgilerini hesapla.

    meals: [breakfast, lunch, dinner] dicts
    """
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for meal in meals:
        nutrition = meal.get("nutrition", {})
        total_calories += nutrition.get("calories", 0)
        total_protein += nutrition.get("protein_g", 0)
        total_carbs += nutrition.get("carbs_g", 0)
        total_fat += nutrition.get("fat_g", 0)

    return {
        "total_calories": total_calories,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "protein_percent": round((total_protein * 4 / total_calories * 100) if total_calories > 0 else 0),
        "carbs_percent": round((total_carbs * 4 / total_calories * 100) if total_calories > 0 else 0),
        "fat_percent": round((total_fat * 9 / total_calories * 100) if total_calories > 0 else 0),
    }


def format_nutrition_info(nutrition: Dict, language: str = "tr") -> str:
    """Beslenme bilgisini formatla"""
    if language == "tr":
        return f"""
📊 **Günlük Beslenme Özeti:**
- Kalori: {nutrition.get('total_calories', 0)} kcal
- Protein: {nutrition.get('total_protein', 0):.1f}g ({nutrition.get('protein_percent', 0)}%)
- Karbonhidrat: {nutrition.get('total_carbs', 0):.1f}g ({nutrition.get('carbs_percent', 0)}%)
- Yağ: {nutrition.get('total_fat', 0):.1f}g ({nutrition.get('fat_percent', 0)}%)
"""
    else:
        return f"""
📊 **Daily Nutrition Summary:**
- Calories: {nutrition.get('total_calories', 0)} kcal
- Protein: {nutrition.get('total_protein', 0):.1f}g ({nutrition.get('protein_percent', 0)}%)
- Carbs: {nutrition.get('total_carbs', 0):.1f}g ({nutrition.get('carbs_percent', 0)}%)
- Fat: {nutrition.get('total_fat', 0):.1f}g ({nutrition.get('fat_percent', 0)}%)
"""


def log_recommendation(user_id: int, date: str, meals: Dict) -> None:
    """Tavsiyeyi loglama"""
    breakfast = meals.get("breakfast", {}).get("name", "N/A")
    lunch = meals.get("lunch", {}).get("name", "N/A")
    dinner = meals.get("dinner", {}).get("name", "N/A")

    log.info(
        f"Recommendation for user {user_id} ({date}): "
        f"Breakfast={breakfast}, Lunch={lunch}, Dinner={dinner}"
    )
