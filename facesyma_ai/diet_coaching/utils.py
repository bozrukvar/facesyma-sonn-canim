"""
utils.py
========
Yardımcı fonksiyonlar - Veri dönüşümleri, validation
"""

import logging
from operator import itemgetter
from typing import Dict, List, Tuple
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
    sifats.sort(key=itemgetter(1), reverse=True)

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


_CHAT_I18N: Dict[str, Dict[str, str]] = {
    "tr": {
        "title": "Beslenme Koçluğu",
        "traits": "Sıfatlarınız",
        "traits_default": "profil verileriniz",
        "breakfast": "☀️ Sabah Öğünü",
        "lunch": "🌤️ Öğlen Öğünü",
        "dinner": "🌙 Akşam Öğünü",
        "fallback": "İyi bir seçim",
        "tip": "Alternatif tavsiyeleri görmek için \"başka seçenekler\" yazabilirsiniz",
    },
    "en": {
        "title": "Meal Recommendations",
        "traits": "Your traits",
        "traits_default": "your profile",
        "breakfast": "☀️ Breakfast",
        "lunch": "🌤️ Lunch",
        "dinner": "🌙 Dinner",
        "fallback": "A great choice",
        "tip": "Type \"other options\" to see alternatives",
    },
    "de": {
        "title": "Ernährungsempfehlungen",
        "traits": "Ihre Eigenschaften",
        "traits_default": "Ihr Profil",
        "breakfast": "☀️ Frühstück",
        "lunch": "🌤️ Mittagessen",
        "dinner": "🌙 Abendessen",
        "fallback": "Eine gute Wahl",
        "tip": "Tippen Sie \"andere Optionen\" für Alternativen",
    },
    "ru": {
        "title": "Рекомендации по питанию",
        "traits": "Ваши качества",
        "traits_default": "ваш профиль",
        "breakfast": "☀️ Завтрак",
        "lunch": "🌤️ Обед",
        "dinner": "🌙 Ужин",
        "fallback": "Хороший выбор",
        "tip": "Напишите «другие варианты» для альтернатив",
    },
    "ar": {
        "title": "توصيات غذائية",
        "traits": "صفاتك",
        "traits_default": "ملفك الشخصي",
        "breakfast": "☀️ الإفطار",
        "lunch": "🌤️ الغداء",
        "dinner": "🌙 العشاء",
        "fallback": "خيار جيد",
        "tip": "اكتب \"خيارات أخرى\" للبدائل",
    },
    "es": {
        "title": "Recomendaciones Nutricionales",
        "traits": "Tus rasgos",
        "traits_default": "tu perfil",
        "breakfast": "☀️ Desayuno",
        "lunch": "🌤️ Almuerzo",
        "dinner": "🌙 Cena",
        "fallback": "Buena opción",
        "tip": "Escribe \"otras opciones\" para ver alternativas",
    },
    "ko": {
        "title": "식단 추천",
        "traits": "당신의 특성",
        "traits_default": "당신의 프로필",
        "breakfast": "☀️ 아침",
        "lunch": "🌤️ 점심",
        "dinner": "🌙 저녁",
        "fallback": "좋은 선택",
        "tip": "\"다른 옵션\"을 입력하면 대안을 볼 수 있습니다",
    },
    "ja": {
        "title": "食事のおすすめ",
        "traits": "あなたの特性",
        "traits_default": "あなたのプロフィール",
        "breakfast": "☀️ 朝食",
        "lunch": "🌤️ 昼食",
        "dinner": "🌙 夕食",
        "fallback": "良い選択",
        "tip": "「他の選択肢」と入力すると代替案が表示されます",
    },
    "zh": {
        "title": "饮食建议",
        "traits": "您的特质",
        "traits_default": "您的个人资料",
        "breakfast": "☀️ 早餐",
        "lunch": "🌤️ 午餐",
        "dinner": "🌙 晚餐",
        "fallback": "不错的选择",
        "tip": "输入「其他选项」查看替代方案",
    },
    "hi": {
        "title": "आहार सिफारिशें",
        "traits": "आपके गुण",
        "traits_default": "आपकी प्रोफ़ाइल",
        "breakfast": "☀️ नाश्ता",
        "lunch": "🌤️ दोपहर का भोजन",
        "dinner": "🌙 रात का खाना",
        "fallback": "अच्छा विकल्प",
        "tip": "विकल्पों के लिए \"अन्य विकल्प\" लिखें",
    },
    "fr": {
        "title": "Recommandations Nutritionnelles",
        "traits": "Vos traits",
        "traits_default": "votre profil",
        "breakfast": "☀️ Petit-déjeuner",
        "lunch": "🌤️ Déjeuner",
        "dinner": "🌙 Dîner",
        "fallback": "Un bon choix",
        "tip": "Tapez \"autres options\" pour voir des alternatives",
    },
    "pt": {
        "title": "Recomendações Nutricionais",
        "traits": "Suas características",
        "traits_default": "seu perfil",
        "breakfast": "☀️ Café da manhã",
        "lunch": "🌤️ Almoço",
        "dinner": "🌙 Jantar",
        "fallback": "Uma boa escolha",
        "tip": "Digite \"outras opções\" para ver alternativas",
    },
    "bn": {
        "title": "খাদ্য সুপারিশ",
        "traits": "আপনার বৈশিষ্ট্য",
        "traits_default": "আপনার প্রোফাইল",
        "breakfast": "☀️ সকালের নাস্তা",
        "lunch": "🌤️ দুপুরের খাবার",
        "dinner": "🌙 রাতের খাবার",
        "fallback": "ভালো পছন্দ",
        "tip": "বিকল্পের জন্য \"অন্য বিকল্প\" লিখুন",
    },
    "id": {
        "title": "Rekomendasi Makanan",
        "traits": "Sifat Anda",
        "traits_default": "profil Anda",
        "breakfast": "☀️ Sarapan",
        "lunch": "🌤️ Makan Siang",
        "dinner": "🌙 Makan Malam",
        "fallback": "Pilihan yang baik",
        "tip": "Ketik \"opsi lain\" untuk melihat alternatif",
    },
    "ur": {
        "title": "غذائی سفارشات",
        "traits": "آپ کی خصوصیات",
        "traits_default": "آپ کا پروفائل",
        "breakfast": "☀️ ناشتہ",
        "lunch": "🌤️ دوپہر کا کھانا",
        "dinner": "🌙 رات کا کھانا",
        "fallback": "اچھا انتخاب",
        "tip": "متبادل کے لیے \"دوسرے اختیارات\" لکھیں",
    },
    "it": {
        "title": "Consigli Nutrizionali",
        "traits": "I tuoi tratti",
        "traits_default": "il tuo profilo",
        "breakfast": "☀️ Colazione",
        "lunch": "🌤️ Pranzo",
        "dinner": "🌙 Cena",
        "fallback": "Una buona scelta",
        "tip": "Scrivi \"altre opzioni\" per vedere alternative",
    },
    "vi": {
        "title": "Gợi Ý Dinh Dưỡng",
        "traits": "Đặc điểm của bạn",
        "traits_default": "hồ sơ của bạn",
        "breakfast": "☀️ Bữa sáng",
        "lunch": "🌤️ Bữa trưa",
        "dinner": "🌙 Bữa tối",
        "fallback": "Lựa chọn tốt",
        "tip": "Nhập \"tùy chọn khác\" để xem thêm",
    },
    "pl": {
        "title": "Zalecenia Żywieniowe",
        "traits": "Twoje cechy",
        "traits_default": "Twój profil",
        "breakfast": "☀️ Śniadanie",
        "lunch": "🌤️ Obiad",
        "dinner": "🌙 Kolacja",
        "fallback": "Dobry wybór",
        "tip": "Wpisz \"inne opcje\", aby zobaczyć alternatywy",
    },
}


def format_recommendation_for_chat(
    recommendation: Dict,
    language: str = "en",
) -> str:
    """
    Tavsiyeyi chat formatında döndür — 18 dil destekli.
    """
    i18n = _CHAT_I18N.get(language, _CHAT_I18N["en"])
    _rget = recommendation.get

    date        = _rget("date", "")
    user_sifats = _rget("user_sifats", [])
    sifat_str   = ", ".join(user_sifats) if user_sifats else i18n["traits_default"]

    def _first(key: str) -> Dict:
        v = _rget(key, [{}])
        return (v[0] if isinstance(v, list) else v) or {}

    b = _first("breakfast"); l = _first("lunch"); d = _first("dinner")
    fb = i18n["fallback"]

    header = f"🍽️ **{date} {i18n['title']}**" if date else f"🍽️ **{i18n['title']}**"

    return f"""{header}

{i18n['traits']}: {sifat_str}

**{i18n['breakfast']}:**
🥣 {b.get('name', 'N/A')}
📝 {b.get('reason', fb)}

**{i18n['lunch']}:**
🥗 {l.get('name', 'N/A')}
📝 {l.get('reason', fb)}

**{i18n['dinner']}:**
🍲 {d.get('name', 'N/A')}
📝 {d.get('reason', fb)}

💡 _{i18n['tip']}_""".strip()


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
        _nutget = nutrition.get
        total_calories += _nutget("calories", 0)
        total_protein += _nutget("protein_g", 0)
        total_carbs += _nutget("carbs_g", 0)
        total_fat += _nutget("fat_g", 0)

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
    _nget  = nutrition.get
    _cal   = _nget('total_calories', 0)
    _prot  = _nget('total_protein', 0)
    _pp    = _nget('protein_percent', 0)
    _carbs = _nget('total_carbs', 0)
    _cp    = _nget('carbs_percent', 0)
    _fat   = _nget('total_fat', 0)
    _fp    = _nget('fat_percent', 0)
    if language == "tr":
        return f"""
📊 **Günlük Beslenme Özeti:**
- Kalori: {_cal} kcal
- Protein: {_prot:.1f}g ({_pp}%)
- Karbonhidrat: {_carbs:.1f}g ({_cp}%)
- Yağ: {_fat:.1f}g ({_fp}%)
"""
    else:
        return f"""
📊 **Daily Nutrition Summary:**
- Calories: {_cal} kcal
- Protein: {_prot:.1f}g ({_pp}%)
- Carbs: {_carbs:.1f}g ({_cp}%)
- Fat: {_fat:.1f}g ({_fp}%)
"""


def log_recommendation(user_id: int, date: str, meals: Dict) -> None:
    """Tavsiyeyi loglama"""
    _mget = meals.get
    _b = _mget("breakfast", [{}]); _l = _mget("lunch", [{}]); _d = _mget("dinner", [{}])
    breakfast = (_b[0] if isinstance(_b, list) else _b).get("name", "N/A")
    lunch     = (_l[0] if isinstance(_l, list) else _l).get("name", "N/A")
    dinner    = (_d[0] if isinstance(_d, list) else _d).get("name", "N/A")

    log.info(
        f"Recommendation for user {user_id} ({date}): "
        f"Breakfast={breakfast}, Lunch={lunch}, Dinner={dinner}"
    )
