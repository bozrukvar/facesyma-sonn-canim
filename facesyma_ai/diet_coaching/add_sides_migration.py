"""
add_sides_migration.py
======================
Tüm ülkelerin yemek JSON dosyalarına "sides" alanı ekler.
Her ülke/mutfak grubu için kültüre uygun garnitür önerileri belirlendi.
Çalıştırma: python -m facesyma_ai.diet_coaching.add_sides_migration
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ── Türkiye: öğün bazlı ID → sides haritası ──────────────────────────────────
TR_SIDES: dict = {
    # lunch soups
    "tr_lunch_001": ["Ekmek", "Yeşillik", "Beyaz Peynir"],
    "tr_lunch_002": ["Ekmek", "Biber Turşusu", "Yeşillik"],
    "tr_lunch_003": ["Ekmek", "Sarımsak", "Limon"],
    # lunch mains
    "tr_lunch_004": ["Çoban Salatası", "Patates Kızartması", "Ayran"],
    "tr_lunch_005": ["Çoban Salatası", "Bulgur Pilavı", "Cacık"],
    "tr_lunch_006": ["Kısır", "Pide Ekmek", "Ayran"],
    "tr_lunch_007": ["Çoban Salatası", "Soğan Salatası", "Ayran"],
    "tr_lunch_008": ["Közlenmiş Biber", "Soğan Salatası", "Ayran"],
    "tr_lunch_009": ["Domates Salatası", "Cacık", "Ayran"],
    "tr_lunch_010": ["Çoban Salatası", "Cacık", "Ayran"],
    "tr_lunch_011": ["Cacık", "Yoğurt", "Domates"],
    "tr_lunch_012": ["Çoban Salatası", "Turşu", "Ayran"],
    "tr_lunch_013": ["Roka", "Maydanoz", "Limonlu Su"],
    "tr_lunch_014": ["Pilav", "Cacık", "Ayran"],
    "tr_lunch_015": ["Çoban Salatası", "Pilav", "Ayran"],
    "tr_lunch_016": ["Roka Salatası", "Patates", "Tarator"],
    "tr_lunch_017": ["Pita Ekmeği", "Zeytinyağı", "Nar Ekşisi"],
    "tr_lunch_018": ["Pide Ekmek", "Beyaz Peynir", "Zeytin"],
    "tr_lunch_019": ["Pita Ekmeği", "Turşu", "Limon"],
    "tr_lunch_020": ["Marul", "Domates", "Pide Ekmek"],
    # dinner mains
    "tr_dinner_001": ["Pilav", "Yoğurt", "Ekmek"],
    "tr_dinner_002": ["Çoban Salatası", "Cacık", "Yoğurt"],
    "tr_dinner_003": ["Pilav", "Turşu", "Ekmek"],
    "tr_dinner_004": ["Roka Salatası", "Tarator", "Limon"],
    "tr_dinner_005": ["Cacık", "Yoğurt", "Domates Salatası"],
    "tr_dinner_006": ["Pilav", "Cacık", "Ekmek"],
    "tr_dinner_007": ["Pilav", "Cacık", "Ekmek"],
    "tr_dinner_008": ["Yeşil Salata", "Ekmek", "Yoğurt"],
    "tr_dinner_009": ["Ekmek", "Domates", "Salatalık"],
    "tr_dinner_010": ["Marul", "Maydanoz", "Limon"],
    # dinner soups
    "tr_dinner_011": ["Ekmek", "Peynir", "Zeytin"],
    "tr_dinner_012": ["Ekmek", "Limon", "Sarımsak"],
    "tr_dinner_013": ["Ekmek", "Soğan", "Biber Turşusu"],
    "tr_dinner_014": ["Cacık", "Pilav", "Yoğurt"],
    "tr_dinner_015": ["Ekmek", "Peynir", "Zeytin"],
}

# ── Mutfak grubu: öğün tipi → varsayılan sides listesi ───────────────────────
# Anahtar: dosya adındaki mutfak kodu  (meals_{key}.json)
CUISINE_SIDES: dict = {
    "tr": {
        "lunch_soup": ["Ekmek", "Yeşillik", "Beyaz Peynir"],
        "lunch":      ["Çoban Salatası", "Cacık", "Ayran"],
        "dinner_soup":["Ekmek", "Peynir", "Zeytin"],
        "dinner":     ["Çoban Salatası", "Pilav", "Cacık"],
    },
    "en": {
        "lunch":  ["Side Salad", "Bread Roll", "Coleslaw"],
        "dinner": ["Garden Salad", "Steamed Vegetables", "Bread"],
    },
    "US": {
        "lunch":  ["Side Salad", "Coleslaw", "Chips"],
        "dinner": ["Garden Salad", "Steamed Broccoli", "Dinner Roll"],
    },
    "GB": {
        "lunch":  ["Side Salad", "Bread Roll", "Pickle"],
        "dinner": ["Garden Salad", "Roasted Potatoes", "Bread"],
    },
    "AU": {
        "lunch":  ["Garden Salad", "Bread Roll", "Coleslaw"],
        "dinner": ["Mixed Salad", "Steamed Vegetables", "Bread"],
    },
    "CA": {
        "lunch":  ["Side Salad", "Dinner Roll", "Coleslaw"],
        "dinner": ["Caesar Salad", "Steamed Vegetables", "Dinner Roll"],
    },
    "fr": {
        "lunch":  ["Salade verte", "Baguette", "Cornichons"],
        "dinner": ["Salade mixte", "Baguette", "Légumes grillés"],
    },
    "BE": {
        "lunch":  ["Salade verte", "Pain", "Cornichons"],
        "dinner": ["Salade mixte", "Pain", "Frites"],
    },
    "CH": {
        "lunch":  ["Salade verte", "Pain", "Cornichons"],
        "dinner": ["Salade mixte", "Pain", "Rösti"],
    },
    "de": {
        "lunch":  ["Beilagensalat", "Brot", "Gurken"],
        "dinner": ["Salat", "Kartoffeln", "Brot"],
    },
    "it": {
        "lunch":  ["Insalata mista", "Pane", "Acqua frizzante"],
        "dinner": ["Insalata verde", "Bruschetta", "Pane"],
    },
    "es": {
        "lunch":  ["Ensalada mixta", "Pan", "Aceitunas"],
        "dinner": ["Ensalada verde", "Pan con tomate", "Aceitunas"],
    },
    "es_latam": {
        "lunch":  ["Ensalada mixta", "Tortillas", "Aguacate"],
        "dinner": ["Ensalada verde", "Arroz", "Frijoles"],
    },
    "MX": {
        "lunch":  ["Guacamole", "Tortillas", "Salsa fresca"],
        "dinner": ["Ensalada verde", "Arroz mexicano", "Frijoles refritos"],
    },
    "AR": {
        "lunch":  ["Ensalada mixta", "Pan", "Chimichurri"],
        "dinner": ["Ensalada verde", "Pan", "Chimichurri"],
    },
    "pt": {
        "lunch":  ["Salada mista", "Pão", "Azeitonas"],
        "dinner": ["Salada verde", "Pão", "Azeitonas"],
    },
    "BR": {
        "lunch":  ["Salada mista", "Arroz branco", "Feijão"],
        "dinner": ["Salada verde", "Arroz", "Farofa"],
    },
    "ru": {
        "lunch":  ["Салат из огурцов", "Хлеб", "Сметана"],
        "dinner": ["Овощной салат", "Хлеб", "Сметана"],
    },
    "ar": {
        "lunch":  ["سلطة خضراء", "خبز عربي", "لبن"],
        "dinner": ["سلطة", "خبز عربي", "ماء"],
    },
    "ar_gulf": {
        "lunch":  ["سلطة خضراء", "خبز", "لبن"],
        "dinner": ["سلطة", "خبز رقاق", "ماء"],
    },
    "ar_levant": {
        "lunch":  ["سلطة فتوش", "خبز عربي", "لبن"],
        "dinner": ["سلطة تبولة", "خبز عربي", "لبن"],
    },
    "ar_maghreb": {
        "lunch":  ["سلطة مغربية", "خبز", "زيتون"],
        "dinner": ["سلطة خضراء", "خبز", "زيتون"],
    },
    "ja": {
        "lunch":  ["味噌汁", "漬物", "ご飯"],
        "dinner": ["味噌汁", "漬物", "白飯"],
    },
    "ko": {
        "lunch":  ["김치", "된장국", "밥"],
        "dinner": ["김치", "나물 반찬", "밥"],
    },
    "zh": {
        "lunch":  ["米饭", "清炒青菜", "汤"],
        "dinner": ["米饭", "清炒时蔬", "汤"],
    },
    "TW": {
        "lunch":  ["白飯", "燙青菜", "湯"],
        "dinner": ["白飯", "炒時蔬", "湯"],
    },
    "hi": {
        "lunch":  ["Raita", "Roti", "Papad"],
        "dinner": ["Raita", "Chapati", "Pickle"],
    },
    "ur": {
        "lunch":  ["Raita", "Naan", "Salad"],
        "dinner": ["Raita", "Roti", "Achar"],
    },
    "bn": {
        "lunch":  ["ভাত", "ডাল", "শাকসবজি"],
        "dinner": ["ভাত", "সালাদ", "দই"],
    },
    "id": {
        "lunch":  ["Nasi putih", "Lalapan", "Sambal"],
        "dinner": ["Nasi putih", "Sayur tumis", "Sambal"],
    },
    "MY": {
        "lunch":  ["Nasi putih", "Acar", "Sambal"],
        "dinner": ["Nasi putih", "Sayur", "Sambal"],
    },
    "PH": {
        "lunch":  ["Steamed rice", "Atchara", "Patis"],
        "dinner": ["Steamed rice", "Ensalada", "Bagoong"],
    },
    "th": {
        "lunch":  ["ข้าวสวย", "ผักสด", "น้ำพริก"],
        "dinner": ["ข้าวสวย", "ผักดอง", "น้ำพริก"],
    },
    "vi": {
        "lunch":  ["Rau sống", "Cơm trắng", "Nước chấm"],
        "dinner": ["Rau sống", "Cơm trắng", "Canh"],
    },
    "pl": {
        "lunch":  ["Surówka", "Chleb razowy", "Ogórek"],
        "dinner": ["Surówka", "Chleb", "Ziemniaki"],
    },
    "NL": {
        "lunch":  ["Salade", "Brood", "Augurken"],
        "dinner": ["Groene salade", "Brood", "Aardappelen"],
    },
    "nordic": {
        "lunch":  ["Green salad", "Rye bread", "Pickles"],
        "dinner": ["Mixed salad", "Rye bread", "Boiled potatoes"],
    },
    "GR": {
        "lunch":  ["Χωριάτικη σαλάτα", "Ψωμί", "Ελιές"],
        "dinner": ["Πράσινη σαλάτα", "Ψωμί", "Τζατζίκι"],
    },
    "IL": {
        "lunch":  ["Israeli salad", "Pita", "Hummus"],
        "dinner": ["Mixed salad", "Pita", "Tahini"],
    },
    "IR": {
        "lunch":  ["سالاد شیرازی", "نان", "ماست"],
        "dinner": ["سالاد سبز", "نان", "ماست"],
    },
    "ZA": {
        "lunch":  ["Garden salad", "Pap", "Chakalaka"],
        "dinner": ["Mixed salad", "Pap", "Chakalaka"],
    },
    "KE": {
        "lunch":  ["Kachumbari salad", "Ugali", "Sukuma wiki"],
        "dinner": ["Kachumbari", "Ugali", "Beans"],
    },
    "ET": {
        "lunch":  ["Ayib", "Injera", "Tikel gomen"],
        "dinner": ["Ayib", "Injera", "Shiro"],
    },
    "NG": {
        "lunch":  ["Garden egg salad", "Eba", "Vegetable soup"],
        "dinner": ["Mixed salad", "Fufu", "Egusi soup"],
    },
}

# Soups keywords (to detect soups and apply soup-specific sides)
_SOUP_KEYWORDS = {
    "çorba", "soup", "soupe", "суп", "حساء", "شوربة", "soup", "汤", "スープ", "국", "ซุป",
    "sopa", "minestra", "zupa", "soep",
}


def _is_soup(meal: dict) -> bool:
    name = (meal.get("name_tr") or meal.get("name_en") or meal.get("name") or "").lower()
    return any(kw in name for kw in _SOUP_KEYWORDS)


def _get_sides(meal: dict, meal_type: str, cuisine_key: str) -> list:
    """Determine appropriate sides for a meal."""
    sides_map = CUISINE_SIDES.get(cuisine_key) or CUISINE_SIDES.get("en")

    if meal_type == "lunch":
        if _is_soup(meal) and "lunch_soup" in sides_map:
            return sides_map["lunch_soup"]
        return sides_map.get("lunch", [])
    elif meal_type == "dinner":
        if _is_soup(meal) and "dinner_soup" in sides_map:
            return sides_map["dinner_soup"]
        return sides_map.get("dinner", [])
    return []  # breakfast: no sides


def _cuisine_key_from_filename(stem: str) -> str:
    """meals_tr → tr, meals_MX → MX, etc."""
    return stem[len("meals_"):]


def add_sides_to_file(path: Path) -> int:
    """Add sides to all lunch/dinner meals in a file. Returns number of meals updated."""
    cuisine_key = _cuisine_key_from_filename(path.stem)
    updated = 0

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    is_flat = isinstance(data, list)
    meals_source = {}

    if is_flat:
        # Flat list: sort by id
        for item in data:
            mid = item.get("id", "")
            if "lunch" in mid:
                meals_source.setdefault("lunch", []).append(item)
            elif "dinner" in mid:
                meals_source.setdefault("dinner", []).append(item)
    else:
        meals_obj = data.get("meals", {})
        meals_source = {
            "lunch":  meals_obj.get("lunch",  []),
            "dinner": meals_obj.get("dinner", []),
        }

    for meal_type, meals in meals_source.items():
        for meal in meals:
            if "sides" in meal:
                continue  # already has sides — skip

            # TR: use per-ID map first
            meal_id = meal.get("id", "")
            if cuisine_key == "tr" and meal_id in TR_SIDES:
                meal["sides"] = TR_SIDES[meal_id]
            else:
                meal["sides"] = _get_sides(meal, meal_type, cuisine_key)
            updated += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


def run():
    files = sorted(DATA_DIR.glob("meals_*.json"))
    total_meals = 0
    for path in files:
        n = add_sides_to_file(path)
        if n:
            print(f"  ✓ {path.name}: {n} öğüne sides eklendi")
        else:
            print(f"  – {path.name}: değişiklik yok")
        total_meals += n
    print(f"\nTamamlandı: {total_meals} öğüne sides eklendi, {len(files)} dosya işlendi.")


if __name__ == "__main__":
    run()
