"""
database.py
===========
Yemek veri havuzunu yönet - JSON dosyalarından yükleme, sorgulama
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .models import CountryMeals, Meal, SifatMapping

log = logging.getLogger(__name__)

# Veri klasörünün yolu
DATA_DIR = Path(__file__).parent / "data"


class MealDatabase:
    """Yemek veri tabanı - Tüm ülkelerin yemeklerini içerir"""

    def __init__(self):
        self.meals: Dict[str, CountryMeals] = {}
        self.sifat_mapping: Optional[SifatMapping] = None
        self._load_all_data()

    def _load_all_data(self):
        """Başlangıçta tüm veriyi yükle"""
        # Şu an aktif olan ülkeleri yükle
        active_countries = ["tr", "hi", "fr"]  # MVP için 3 ülke
        for lang_code in active_countries:
            self._load_country_meals(lang_code)

        # Sıfat mapping'i yükle
        self._load_sifat_mapping()
        log.info(f"✓ Veri tabanı initialized: {len(self.meals)} ülke, sıfat mapping yüklü")

    def _load_country_meals(self, lang_code: str):
        """Bir ülkenin yemeklerini JSON'dan yükle"""
        meals_file = DATA_DIR / f"meals_{lang_code}.json"

        if not meals_file.exists():
            log.warning(f"⚠ Meals file not found: {meals_file}")
            return

        try:
            with open(meals_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            country_meals = CountryMeals(**data)
            self.meals[lang_code] = country_meals
            log.info(f"✓ Loaded meals for {data['country']} ({lang_code})")
        except Exception as e:
            log.error(f"✗ Error loading meals for {lang_code}: {e}")

    def _load_sifat_mapping(self):
        """Sıfat-yemek mapping'ini yükle"""
        mapping_file = DATA_DIR / "sifat_mapping.json"

        if not mapping_file.exists():
            log.warning(f"⚠ Sifat mapping file not found: {mapping_file}")
            return

        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sifat_mapping = SifatMapping(**data)
            log.info(f"✓ Loaded sifat mapping ({len(self.sifat_mapping.sifat_meal_preferences)} sıfatlar)")
        except Exception as e:
            log.error(f"✗ Error loading sifat mapping: {e}")

    def get_country_meals(self, lang_code: str) -> Optional[CountryMeals]:
        """Bir ülkenin yemeklerini al"""
        return self.meals.get(lang_code)

    def get_meal_by_id(self, lang_code: str, meal_id: str) -> Optional[Meal]:
        """Meal ID'ye göre yemek al"""
        country = self.get_country_meals(lang_code)
        if not country:
            return None

        # Sabah, öğlen, akşam içinde ara
        for meal in country.meals.breakfast:
            if meal.id == meal_id:
                return meal
        for meal in country.meals.lunch:
            if meal.id == meal_id:
                return meal
        for meal in country.meals.dinner:
            if meal.id == meal_id:
                return meal

        return None

    def get_meals_by_type(
        self, lang_code: str, meal_type: str
    ) -> List[Meal]:
        """Öğün tipine göre yemekleri al (breakfast, lunch, dinner)"""
        country = self.get_country_meals(lang_code)
        if not country:
            return []

        if meal_type == "breakfast":
            return country.meals.breakfast
        elif meal_type == "lunch":
            return country.meals.lunch
        elif meal_type == "dinner":
            return country.meals.dinner

        return []

    def get_sifat_preferences(self, sifat: str) -> Optional[Dict]:
        """Bir sıfat için yemek tercihlerini al"""
        if not self.sifat_mapping:
            return None
        return self.sifat_mapping.sifat_meal_preferences.get(sifat)

    def get_sifat_weight(self, sifat: str) -> float:
        """Bir sıfatın ağırlığını al"""
        prefs = self.get_sifat_preferences(sifat)
        if prefs:
            return prefs.weight
        return 1.0

    def get_available_countries(self) -> List[Dict[str, str]]:
        """Mevcut ülkelerin listesi"""
        countries = []
        for lang_code, country_data in self.meals.items():
            countries.append({
                "name": country_data.country,
                "language_code": lang_code,
                "meal_count": (
                    len(country_data.meals.breakfast)
                    + len(country_data.meals.lunch)
                    + len(country_data.meals.dinner)
                ),
            })
        return countries

    def add_country_meals(self, country_meals: CountryMeals):
        """Yeni ülke yemekleri ekle"""
        lang_code = country_meals.language_code
        self.meals[lang_code] = country_meals
        log.info(f"✓ Added meals for {country_meals.country} ({lang_code})")

    def reload_data(self):
        """Tüm veriyi yeniden yükle"""
        self.meals.clear()
        self._load_all_data()
        log.info("✓ Database reloaded")


# Global veri tabanı singleton
_db: Optional[MealDatabase] = None


def get_database() -> MealDatabase:
    """Global veri tabanını al (lazy initialization)"""
    global _db
    if _db is None:
        _db = MealDatabase()
    return _db


# ── Helper Functions ────────────────────────────────────────────────────────

def load_meals_for_country(lang_code: str) -> Optional[Dict]:
    """Bir ülkeyi yükle ve döndür"""
    db = get_database()
    country = db.get_country_meals(lang_code)
    if country:
        return country.dict()
    return None


def get_all_countries() -> List[Dict]:
    """Tüm mevcut ülkeleri döndür"""
    db = get_database()
    return db.get_available_countries()


def get_country_meals(lang_code: str) -> Optional[Dict]:
    """Bir ülkenin yemeklerini döndür"""
    db = get_database()
    country = db.get_country_meals(lang_code)
    if country:
        return country.dict()
    return None


def get_meals_by_type_and_country(lang_code: str, meal_type: str) -> List[Dict]:
    """Ülke ve öğün tipine göre yemekleri döndür"""
    db = get_database()
    meals = db.get_meals_by_type(lang_code, meal_type)
    return [meal.dict() for meal in meals]
