"""
database.py
===========
Yemek veri havuzunu yönet — 120 ülke, fallback zinciri ile.

Anahtar: ISO 3166-1 alpha-2 ülke kodu (TR, MX, SA, US, ...)

Fallback zinciri (sırayla denenecek):
  1. meals_{CC}.json          — ülkeye özgü (ör: meals_MX.json)
  2. meals_{cuisine_key}.json — mutfak grubu (ör: meals_ar_gulf.json)
  3. meals_{lang}.json        — dil default  (ör: meals_ar.json)
  4. meals_en.json            — son çare
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import CountryMeals, Meal, SifatMapping

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"

# ── 120 Ülke → Mutfak Grubu Eşlemesi ──────────────────────────────────────────
# Değer: cuisine_key → meals_{cuisine_key}.json dosyasına bakılır
COUNTRY_CUISINE_MAP: Dict[str, str] = {
    # ── Türkiye ve Türk Dünyası ──────────────────────────────────────────────
    'TR': 'tr',        'AZ': 'tr',        'UZ': 'tr',
    'KZ': 'tr',        'KG': 'tr',        'TM': 'tr',

    # ── Körfez Arap ──────────────────────────────────────────────────────────
    'SA': 'ar_gulf',   'AE': 'ar_gulf',   'KW': 'ar_gulf',
    'QA': 'ar_gulf',   'BH': 'ar_gulf',   'OM': 'ar_gulf',

    # ── Levant Arap ──────────────────────────────────────────────────────────
    'LB': 'ar_levant', 'SY': 'ar_levant', 'JO': 'ar_levant',
    'IQ': 'ar_levant', 'PS': 'ar_levant',

    # ── Kuzey Afrika ─────────────────────────────────────────────────────────
    'EG': 'ar',        'SD': 'ar',        'LY': 'ar_maghreb',
    'MA': 'ar_maghreb','DZ': 'ar_maghreb','TN': 'ar_maghreb',
    'MR': 'ar_maghreb',

    # ── İspanya ──────────────────────────────────────────────────────────────
    'ES': 'es',

    # ── Meksika / Orta Amerika ───────────────────────────────────────────────
    'MX': 'MX',        'GT': 'MX',        'HN': 'MX',
    'SV': 'MX',        'NI': 'MX',        'CR': 'MX',
    'PA': 'MX',        'CU': 'MX',        'DO': 'MX',
    'PR': 'MX',

    # ── Güney Amerika ────────────────────────────────────────────────────────
    'AR': 'AR',        'UY': 'AR',        'PY': 'AR',
    'CO': 'es_latam',  'PE': 'es_latam',  'CL': 'es_latam',
    'VE': 'es_latam',  'EC': 'es_latam',  'BO': 'es_latam',
    'BR': 'BR',

    # ── Portekiz ─────────────────────────────────────────────────────────────
    'PT': 'pt',        'AO': 'pt',        'MZ': 'pt',

    # ── İngilizce / Anglosakson ──────────────────────────────────────────────
    'US': 'US',        'GB': 'GB',        'IE': 'GB',
    'AU': 'AU',        'NZ': 'AU',        'CA': 'CA',

    # ── Fransız ──────────────────────────────────────────────────────────────
    'FR': 'fr',        'BE': 'BE',        'LU': 'BE',
    'CH': 'CH',

    # ── Almanca ──────────────────────────────────────────────────────────────
    'DE': 'de',        'AT': 'de',

    # ── Rusça / Doğu Avrupa ──────────────────────────────────────────────────
    'RU': 'ru',        'UA': 'ru',        'BY': 'ru',

    # ── Japonya ──────────────────────────────────────────────────────────────
    'JP': 'ja',

    # ── Kore ─────────────────────────────────────────────────────────────────
    'KR': 'ko',

    # ── Çin bölgesi ──────────────────────────────────────────────────────────
    'CN': 'zh',        'TW': 'TW',        'HK': 'TW',
    'MO': 'TW',

    # ── Hint Alt Kıtası ──────────────────────────────────────────────────────
    'IN': 'hi',        'LK': 'hi',        'NP': 'hi',
    'PK': 'ur',        'BD': 'bn',

    # ── Güneydoğu Asya ───────────────────────────────────────────────────────
    'ID': 'id',        'MY': 'MY',        'SG': 'MY',
    'BN': 'MY',        'TH': 'th',        'VN': 'vi',
    'PH': 'PH',        'MM': 'th',        'KH': 'th',
    'LA': 'th',

    # ── İtalya ───────────────────────────────────────────────────────────────
    'IT': 'it',        'SM': 'it',        'VA': 'it',
    'MT': 'it',

    # ── Polonya / Doğu Avrupa ────────────────────────────────────────────────
    'PL': 'pl',        'CZ': 'pl',        'SK': 'pl',
    'HU': 'pl',        'RO': 'pl',

    # ── Hollanda / Benelüks ──────────────────────────────────────────────────
    'NL': 'NL',

    # ── İskandinav ───────────────────────────────────────────────────────────
    'SE': 'nordic',    'NO': 'nordic',    'DK': 'nordic',
    'FI': 'nordic',    'IS': 'nordic',

    # ── Yunanistan / Balkanlar ───────────────────────────────────────────────
    'GR': 'GR',        'CY': 'GR',        'BG': 'GR',
    'RS': 'GR',        'MK': 'GR',        'AL': 'GR',
    'HR': 'it',        'SI': 'it',

    # ── İsrail ───────────────────────────────────────────────────────────────
    'IL': 'IL',

    # ── İran / Orta Doğu ─────────────────────────────────────────────────────
    'IR': 'IR',        'AF': 'IR',

    # ── Güney Afrika ─────────────────────────────────────────────────────────
    'ZA': 'ZA',        'NA': 'ZA',        'BW': 'ZA',
    'ZW': 'ZA',

    # ── Doğu Afrika ──────────────────────────────────────────────────────────
    'KE': 'KE',        'TZ': 'KE',        'UG': 'KE',
    'RW': 'KE',        'ET': 'ET',        'ER': 'ET',

    # ── Batı Afrika ──────────────────────────────────────────────────────────
    'NG': 'NG',        'GH': 'NG',        'SN': 'NG',
    'CI': 'NG',        'CM': 'NG',
}

# ── Mutfak Grubu → Dil Fallback ───────────────────────────────────────────────
# Eğer meals_{cuisine_key}.json yoksa bu dil dosyasına düşer
_CUISINE_LANG_FALLBACK: Dict[str, str] = {
    'ar_gulf': 'ar',    'ar_levant': 'ar',  'ar_maghreb': 'ar',
    'MX': 'es',         'AR': 'es',         'es_latam': 'es',
    'BR': 'pt',         'US': 'en',         'GB': 'en',
    'AU': 'en',         'CA': 'en',         'BE': 'fr',
    'CH': 'fr',         'TW': 'zh',         'MY': 'id',
    'PH': 'en',         'NL': 'de',         'nordic': 'de',
    'GR': 'tr',         'IL': 'ar',         'IR': 'tr',
    'ZA': 'en',         'KE': 'en',         'ET': 'en',
    'NG': 'en',
}

# ── Ülke Kodu → Dil Kodu (görüntüleme / mesaj dili) ──────────────────────────
COUNTRY_LANG_MAP: Dict[str, str] = {
    'TR': 'tr', 'AZ': 'tr', 'UZ': 'tr', 'KZ': 'tr', 'KG': 'tr', 'TM': 'tr',
    'SA': 'ar', 'AE': 'ar', 'KW': 'ar', 'QA': 'ar', 'BH': 'ar', 'OM': 'ar',
    'LB': 'ar', 'SY': 'ar', 'JO': 'ar', 'IQ': 'ar', 'PS': 'ar',
    'EG': 'ar', 'MA': 'ar', 'DZ': 'ar', 'TN': 'ar', 'LY': 'ar', 'SD': 'ar',
    'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es', 'PE': 'es', 'CL': 'es',
    'VE': 'es', 'EC': 'es', 'BO': 'es', 'PY': 'es', 'UY': 'es',
    'GT': 'es', 'HN': 'es', 'SV': 'es', 'NI': 'es', 'CR': 'es', 'PA': 'es',
    'CU': 'es', 'DO': 'es', 'PR': 'es',
    'PT': 'pt', 'BR': 'pt', 'AO': 'pt', 'MZ': 'pt',
    'US': 'en', 'GB': 'en', 'IE': 'en', 'AU': 'en', 'NZ': 'en', 'CA': 'en',
    'ZA': 'en', 'GH': 'en', 'KE': 'en', 'TZ': 'en', 'UG': 'en', 'NG': 'en',
    'FR': 'fr', 'BE': 'fr', 'LU': 'fr', 'CH': 'fr', 'SN': 'fr', 'CI': 'fr',
    'DE': 'de', 'AT': 'de',
    'RU': 'ru', 'UA': 'ru', 'BY': 'ru',
    'JP': 'ja', 'KR': 'ko',
    'CN': 'zh', 'TW': 'zh', 'HK': 'zh', 'MO': 'zh', 'SG': 'zh',
    'IN': 'hi', 'LK': 'hi', 'NP': 'hi',
    'PK': 'ur', 'BD': 'bn',
    'ID': 'id', 'MY': 'id', 'BN': 'id',
    'TH': 'th', 'VN': 'vi', 'PH': 'en', 'MM': 'th', 'KH': 'th', 'LA': 'th',
    'IT': 'it', 'MT': 'it',
    'PL': 'pl', 'CZ': 'pl', 'SK': 'pl', 'HU': 'pl', 'RO': 'pl',
    'NL': 'nl', 'SE': 'sv', 'NO': 'no', 'DK': 'da', 'FI': 'fi', 'IS': 'is',
    'GR': 'el', 'CY': 'el', 'BG': 'bg', 'RS': 'sr', 'HR': 'hr',
    'IL': 'he', 'IR': 'fa', 'AF': 'fa',
    'ET': 'am', 'ER': 'ti',
}


class MealDatabase:
    """
    Yemek veri tabanı.

    Yükleme stratejisi (lazy, per-country):
      1. meals_{CC}.json           — ülkeye özgü
      2. meals_{cuisine_key}.json  — mutfak grubu
      3. meals_{lang}.json         — dil varsayılanı
      4. meals_en.json             — son çare
    """

    def __init__(self):
        self._meals: Dict[str, CountryMeals] = {}   # country_code → CountryMeals
        self._sifat_mapping: Optional[SifatMapping] = None
        self._load_sifat_mapping()

    # ── Sıfat Mapping ────────────────────────────────────────────────────────

    def _load_sifat_mapping(self):
        mapping_file = DATA_DIR / "sifat_mapping.json"
        if not mapping_file.exists():
            log.warning("Sifat mapping file not found")
            return
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                self._sifat_mapping = SifatMapping(**json.load(f))
            log.info(f"✓ Sifat mapping yüklendi ({len(self._sifat_mapping.sifat_meal_preferences)} sıfat)")
        except Exception as e:
            log.error(f"Sifat mapping yüklenemedi: {e}")

    # ── Dosya Çözümleme ───────────────────────────────────────────────────────

    def _resolve_meals_file(self, country_code: str) -> Optional[Path]:
        """
        Ülke koduna göre en uygun yemek JSON dosyasını bul.
        Fallback zinciri: CC → cuisine_key → lang → en
        """
        cc = country_code.upper()

        # 1. Ülkeye özgü dosya
        p = DATA_DIR / f"meals_{cc}.json"
        if p.exists():
            return p

        # 2. Mutfak grubu dosyası
        cuisine_key = COUNTRY_CUISINE_MAP.get(cc, '')
        if cuisine_key:
            p = DATA_DIR / f"meals_{cuisine_key}.json"
            if p.exists():
                return p

        # 3. Dil fallback
        lang = _CUISINE_LANG_FALLBACK.get(cuisine_key) or COUNTRY_LANG_MAP.get(cc, '')
        if lang:
            p = DATA_DIR / f"meals_{lang}.json"
            if p.exists():
                return p

        # 4. Son çare
        p = DATA_DIR / "meals_en.json"
        if p.exists():
            return p

        return None

    # ── Yükleme ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_meal(meal: dict) -> dict:
        """Any old-format meal dict → new Pydantic schema (in-place)."""
        # 1. nutrition: short keys → _g suffix
        n = meal.get('nutrition', {})
        if 'protein' in n and 'protein_g' not in n:
            n['protein_g'] = n.pop('protein')
        if 'carbs' in n and 'carbs_g' not in n:
            n['carbs_g'] = n.pop('carbs')
        if 'fat' in n and 'fat_g' not in n:
            n['fat_g'] = n.pop('fat')
        # 2. dietary: flat fields → nested dict
        if 'dietary' not in meal:
            meal['dietary'] = {
                'omnivore':    meal.pop('omnivore',    True),
                'vegetarian':  meal.pop('vegetarian',  False),
                'vegan':       meal.pop('vegan',       False),
                'gluten_free': meal.pop('gluten_free', False),
            }
        # 3. name: language-specific key → name_tr fallback
        if 'name_tr' not in meal:
            for key in ('name_he', 'name_ja', 'name_ko', 'name_zh', 'name_ar',
                        'name_id', 'name', 'title'):
                if key in meal:
                    meal['name_tr'] = meal[key]
                    break
            else:
                meal['name_tr'] = meal.get('name_en', 'Unknown')
        return meal

    @staticmethod
    def _normalize_doc(data: dict) -> dict:
        """Document-level normalization (in-place)."""
        # country_name → country
        if 'country' not in data and 'country_name' in data:
            data['country'] = data.pop('country_name')
        return data

    @staticmethod
    def _flat_list_to_nested(items: list, country: str, lang: str) -> dict:
        """Convert a flat meal list to CountryMeals dict by inferring type from id."""
        by_type: dict = {'breakfast': [], 'lunch': [], 'dinner': []}
        for item in items:
            meal_id = item.get('id', '')
            if 'breakfast' in meal_id:
                by_type['breakfast'].append(item)
            elif 'lunch' in meal_id:
                by_type['lunch'].append(item)
            elif 'dinner' in meal_id:
                by_type['dinner'].append(item)
            else:
                by_type['dinner'].append(item)
        return {
            'country': country,
            'language_code': lang,
            'meals': by_type,
        }

    def _load_country(self, country_code: str) -> Optional[CountryMeals]:
        """Bir ülkenin yemeklerini lazy yükle."""
        cc = country_code.upper()
        path = self._resolve_meals_file(cc)
        if not path:
            log.error(f"Yemek dosyası bulunamadı: {cc}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            # Handle flat-list format
            if isinstance(raw, list):
                lang = COUNTRY_LANG_MAP.get(cc, 'en')
                data = self._flat_list_to_nested(raw, cc, lang)
            else:
                data = raw
                self._normalize_doc(data)

            # Normalize each meal
            for meal_type in ('breakfast', 'lunch', 'dinner'):
                for meal in data.get('meals', {}).get(meal_type, []):
                    self._normalize_meal(meal)

            # Override metadata
            data['country_code'] = cc
            if 'language_code' not in data or not data['language_code']:
                data['language_code'] = COUNTRY_LANG_MAP.get(cc, 'en')

            cm = CountryMeals(**data)
            self._meals[cc] = cm
            log.info(f"✓ {cc} → {path.name} ({len(cm.meals.breakfast) + len(cm.meals.lunch) + len(cm.meals.dinner)} yemek)")
            return cm
        except Exception as e:
            log.error(f"Yemek yüklenemedi [{cc}]: {e}")
            return None

    # ── Sorgu Arayüzü ─────────────────────────────────────────────────────────

    def get_country_meals(self, country_code: str) -> Optional[CountryMeals]:
        """Ülke yemeklerini al — yoksa lazy yükle."""
        cc = country_code.upper()
        if cc not in self._meals:
            self._load_country(cc)
        return self._meals.get(cc)

    def get_meal_by_id(self, country_code: str, meal_id: str) -> Optional[Meal]:
        country = self.get_country_meals(country_code)
        if not country:
            return None
        _cm = country.meals
        for meal in (*_cm.breakfast, *_cm.lunch, *_cm.dinner):
            if meal.id == meal_id:
                return meal
        return None

    def get_meals_by_type(self, country_code: str, meal_type: str) -> List[Meal]:
        country = self.get_country_meals(country_code)
        if not country:
            return []
        _cm = country.meals
        if meal_type == "breakfast":
            return _cm.breakfast
        if meal_type == "lunch":
            return _cm.lunch
        if meal_type == "dinner":
            return _cm.dinner
        return []

    def get_sifat_preferences(self, sifat: str):
        if not self._sifat_mapping:
            return None
        return self._sifat_mapping.sifat_meal_preferences.get(sifat)

    def get_sifat_weight(self, sifat: str) -> float:
        prefs = self.get_sifat_preferences(sifat)
        return prefs.weight if prefs else 1.0

    def get_available_countries(self) -> List[Dict]:
        """Şu an cache'te olan ülkeleri listele."""
        result = []
        for cc, cd in self._meals.items():
            _cdm = cd.meals
            result.append({
                "name": cd.country,
                "country_code": cc,
                "language_code": cd.language_code,
                "meal_count": len(_cdm.breakfast) + len(_cdm.lunch) + len(_cdm.dinner),
            })
        return result

    def get_supported_country_codes(self) -> List[str]:
        """Tüm desteklenen ülke kodlarını döndür (120+)."""
        return sorted(COUNTRY_CUISINE_MAP.keys())

    def reload_data(self):
        self._meals.clear()
        self._load_sifat_mapping()
        log.info("✓ Database temizlendi (lazy yeniden yüklenecek)")


# ── Singleton ─────────────────────────────────────────────────────────────────
_db: Optional[MealDatabase] = None


def get_database() -> MealDatabase:
    global _db
    if _db is None:
        _db = MealDatabase()
    return _db


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_country_meals(country_code: str) -> Optional[Dict]:
    db = get_database()
    country = db.get_country_meals(country_code)
    return country.dict() if country else None


def get_all_countries() -> List[Dict]:
    db = get_database()
    return db.get_available_countries()


def get_meals_by_type_and_country(country_code: str, meal_type: str) -> List[Dict]:
    db = get_database()
    meals = db.get_meals_by_type(country_code, meal_type)
    return [meal.dict() for meal in meals]
