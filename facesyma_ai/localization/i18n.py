"""
Internationalization (i18n) Module
Handles multi-language support for 10 languages
"""
import json
import os
from operator import itemgetter
from typing import Dict, Optional
import logging

log = logging.getLogger(__name__)

_DATE_FORMATS = {
    "tr": "dd.MM.yyyy", "en": "MM/dd/yyyy", "ar": "dd/MM/yyyy",
    "pt": "dd/MM/yyyy", "it": "dd/MM/yyyy", "de": "dd.MM.yyyy",
    "es": "dd/MM/yyyy", "ja": "yyyy/MM/dd", "ko": "yyyy.MM.dd",
    "ru": "dd.MM.yyyy", "fr": "dd/MM/yyyy", "zh": "yyyy/MM/dd",
    "hi": "dd/MM/yyyy", "bn": "dd/MM/yyyy", "id": "dd/MM/yyyy",
    "ur": "dd/MM/yyyy", "vi": "dd/MM/yyyy", "pl": "dd.MM.yyyy",
}
_TIME_FORMATS = {
    "tr": "HH:mm", "en": "hh:mm a", "ar": "HH:mm", "pt": "HH:mm",
    "it": "HH:mm", "de": "HH:mm", "es": "HH:mm", "ja": "HH:mm",
    "ko": "HH:mm", "ru": "HH:mm", "fr": "HH:mm", "zh": "HH:mm",
    "hi": "HH:mm", "bn": "HH:mm", "id": "HH:mm", "ur": "HH:mm",
    "vi": "HH:mm", "pl": "HH:mm",
}
_CURRENCY_SYMBOLS = {
    "tr": "₺", "en": "$",  "ar": "ر.س", "pt": "R$", "it": "€",
    "de": "€", "es": "€",  "ja": "¥",   "ko": "₩",  "ru": "₽",
    "fr": "€", "zh": "¥",  "hi": "₹",   "bn": "৳",  "id": "Rp",
    "ur": "₨", "vi": "₫",  "pl": "zł",
}
_NUMBER_FORMATS = {
    "tr": {"decimal": ",", "thousands": "."},
    "en": {"decimal": ".", "thousands": ","},
    "ar": {"decimal": "،", "thousands": "."},
    "pt": {"decimal": ",", "thousands": "."},
    "it": {"decimal": ",", "thousands": "."},
    "de": {"decimal": ",", "thousands": "."},
    "es": {"decimal": ",", "thousands": "."},
    "ja": {"decimal": ".", "thousands": ","},
    "ko": {"decimal": ".", "thousands": ","},
    "ru": {"decimal": ",", "thousands": " "},
    "fr": {"decimal": ",", "thousands": " "},
    "zh": {"decimal": ".", "thousands": ","},
    "hi": {"decimal": ".", "thousands": ","},
    "bn": {"decimal": ".", "thousands": ","},
    "id": {"decimal": ",", "thousands": "."},
    "ur": {"decimal": ".", "thousands": ","},
    "vi": {"decimal": ",", "thousands": "."},
    "pl": {"decimal": ",", "thousands": " "},
}

class LocalizationManager:
    """Manages localization for 18 languages"""

    SUPPORTED_LANGUAGES = {
        "tr": "Türkçe",
        "en": "English",
        "ar": "العربية",
        "pt": "Português",
        "it": "Italiano",
        "de": "Deutsch",
        "es": "Español",
        "ja": "日本語",
        "ko": "한국어",
        "ru": "Русский",
        "fr": "Français",
        "zh": "中文",
        "hi": "हिन्दी",
        "bn": "বাংলা",
        "id": "Bahasa Indonesia",
        "ur": "اردو",
        "vi": "Tiếng Việt",
        "pl": "Polski"
    }

    def __init__(self, localization_path: str = None):
        # Try to load 18-language version first, then fallback to 10-language
        _ospe = os.path.exists
        if localization_path is None:
            if _ospe("./localization_18languages.json"):
                localization_path = "./localization_18languages.json"
            elif _ospe("./localization.json"):
                localization_path = "./localization.json"
            else:
                localization_path = "./localization.json"

        self.localization_path = localization_path
        self.strings: Dict[str, Dict[str, str]] = {}
        self.language_metadata: Dict[str, Dict] = {}
        self.default_language = "en"
        self.load_strings()

    def load_strings(self):
        """Load localization strings and metadata"""
        if os.path.exists(self.localization_path):
            try:
                with open(self.localization_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Load UI strings (works for both old and new format)
                    _dget = data.get
                    if "strings" in data:
                        self.strings = _dget("strings", {})
                    elif "ui_strings" in data:
                        self.strings = _dget("ui_strings", {})
                    # Load language metadata if available (18-language format)
                    if "language_metadata" in data:
                        self.language_metadata = _dget("language_metadata", {})
                log.info(f"Loaded localization for {len(self.strings)} keys, {len(self.language_metadata) or len(self.SUPPORTED_LANGUAGES)} languages")
            except Exception as e:
                log.error(f"Error loading localization: {e}")

    def get_string(self, key: str, language: str = "en") -> str:
        """Get localized string"""
        if key not in self.strings:
            return f"[{key}]"  # Return key if not found

        strings = self.strings[key]
        if language in strings:
            return strings[language]

        # Fallback to English
        if self.default_language in strings:
            return strings[self.default_language]

        # Return first available language
        return list(strings.values())[0] if strings else f"[{key}]"

    def translate(self, key: str, lang: str = "en") -> str:
        """Translate a key to specified language"""
        return self.get_string(key, lang)

    def get_all_strings(self, language: str = "en") -> Dict[str, str]:
        """Get all strings for a language"""
        result = {}
        for key, translations in self.strings.items():
            result[key] = self.get_string(key, language)
        return result

    def supports_language(self, lang: str) -> bool:
        """Check if language is supported"""
        return lang in self.SUPPORTED_LANGUAGES

    def get_language_name(self, lang: str) -> str:
        """Get native name of language"""
        return self.SUPPORTED_LANGUAGES.get(lang, "Unknown")

    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()

    def detect_language_from_browser(self, accept_language: str) -> str:
        """Detect language from HTTP Accept-Language header"""
        if not accept_language:
            return self.default_language

        # Parse Accept-Language header
        languages = []
        for lang in accept_language.split(","):
            parts = lang.split(";")
            lang_code = parts[0].strip().lower()
            quality = 1.0

            if len(parts) > 1:
                q_parts = parts[1].split("=")
                if len(q_parts) > 1:
                    try:
                        quality = float(q_parts[1])
                    except Exception:
                        quality = 0.0

            # Extract primary language code
            primary = lang_code.split("-")[0]
            languages.append((primary, quality))

        # Sort by quality
        languages.sort(key=itemgetter(1), reverse=True)

        # Return first supported language
        for lang, _ in languages:
            if lang in self.SUPPORTED_LANGUAGES:
                return lang

        return self.default_language

    def get_language_direction(self, lang: str) -> str:
        """Get text direction for language (LTR or RTL)"""
        _lm = self.language_metadata
        # Check metadata first (18-language format)
        if _lm and lang in _lm:
            return _lm[lang].get("direction", "ltr")
        # Fallback to hardcoded list
        rtl_languages = ["ar", "ur"]
        return "rtl" if lang in rtl_languages else "ltr"

    def get_date_format(self, lang: str) -> str:
        """Get date format for language"""
        _lm = self.language_metadata
        # Check metadata first (18-language format)
        if _lm and lang in _lm:
            return _lm[lang].get("date_format", "MM/dd/yyyy")
        return _DATE_FORMATS.get(lang, "MM/dd/yyyy")

    def get_time_format(self, lang: str) -> str:
        """Get time format for language"""
        _lm = self.language_metadata
        # Check metadata first (18-language format)
        if _lm and lang in _lm:
            return _lm[lang].get("time_format", "HH:mm")
        return _TIME_FORMATS.get(lang, "HH:mm")

    def pluralize(self, key: str, count: int, lang: str = "en") -> str:
        """Handle pluralization (simple implementation)"""
        if count == 1:
            return self.get_string(key + "_singular", lang)
        else:
            return self.get_string(key + "_plural", lang)

    def get_number_format(self, lang: str) -> Dict[str, str]:
        """Get number formatting for language"""
        _lm = self.language_metadata
        # Check metadata first (18-language format)
        if _lm and lang in _lm:
            meta = _lm[lang]
            _mget = meta.get
            return {
                "decimal": _mget("decimal_separator", "."),
                "thousands": _mget("thousands_separator", ",")
            }
        return _NUMBER_FORMATS.get(lang, {"decimal": ".", "thousands": ","})

    def get_currency_symbol(self, lang: str) -> str:
        """Get currency symbol for language/locale"""
        _lm = self.language_metadata
        # Check metadata first (18-language format)
        if _lm and lang in _lm:
            return _lm[lang].get("currency", "$")
        return _CURRENCY_SYMBOLS.get(lang, "$")

    # Module-specific localizations
    def get_module_name(self, module: str, lang: str = "en") -> str:
        """Get localized module name"""
        return self.get_string(module, lang)

    def get_trait_explanation(self, trait: str, lang: str = "en") -> str:
        """Get localized trait explanation (if exists)"""
        return self.get_string(f"trait_{trait}", lang)

    def get_category_name(self, category: str, lang: str = "en") -> str:
        """Get localized category name"""
        return self.get_string(category, lang)
