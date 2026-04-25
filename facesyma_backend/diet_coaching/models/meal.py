"""Meal models"""

from typing import Optional, Dict, List


class Meal:
    """Meal model for the meal game"""
    def __init__(
        self,
        meal_id: str,
        name: str,
        cuisine: str,
        country: str,
        difficulty: int = 5,
        image_url: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.meal_id = meal_id
        self.name = name
        self.cuisine = cuisine
        self.country = country
        self.difficulty = difficulty
        self.image_url = image_url
        self.description = description


class MealSelectionRequest:
    """Request model for meal selection"""
    def __init__(
        self,
        user_id: int,
        meal_id: str,
        confidence: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        self.user_id = user_id
        self.meal_id = meal_id
        self.confidence = confidence or 0.5
        self.metadata = metadata or {}


class MealSifatGuessRequest:
    """Request model for sifat guess in meal context"""
    def __init__(
        self,
        user_id: int,
        meal_id: str,
        sifat_id: int,
        confidence: Optional[float] = None
    ):
        self.user_id = user_id
        self.meal_id = meal_id
        self.sifat_id = sifat_id
        self.confidence = confidence or 0.5


class MealLeaderboardEntry:
    """Leaderboard entry for meal game"""
    def __init__(
        self,
        user_id: int,
        username: str,
        score: int,
        meals_completed: int,
        country: str,
        week: int,
        rank: Optional[int] = None
    ):
        self.user_id = user_id
        self.username = username
        self.score = score
        self.meals_completed = meals_completed
        self.country = country
        self.week = week
        self.rank = rank


COUNTRY_CODES: Dict[str, str] = {
    'TR': 'Türkiye', 'US': 'United States', 'GB': 'United Kingdom',
    'DE': 'Germany', 'FR': 'France', 'IT': 'Italy', 'ES': 'Spain',
    'PT': 'Portugal', 'NL': 'Netherlands', 'BE': 'Belgium',
    'CH': 'Switzerland', 'AT': 'Austria', 'PL': 'Poland', 'RU': 'Russia',
    'JP': 'Japan', 'CN': 'China', 'KR': 'South Korea', 'IN': 'India',
    'BR': 'Brazil', 'MX': 'Mexico', 'AR': 'Argentina', 'AU': 'Australia',
    'CA': 'Canada', 'ZA': 'South Africa', 'EG': 'Egypt', 'NG': 'Nigeria',
    'SA': 'Saudi Arabia', 'AE': 'UAE', 'IR': 'Iran', 'PK': 'Pakistan',
    'ID': 'Indonesia', 'TH': 'Thailand', 'VN': 'Vietnam', 'MY': 'Malaysia',
    'GR': 'Greece', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark',
    'FI': 'Finland', 'CZ': 'Czech Republic', 'HU': 'Hungary', 'RO': 'Romania',
    'BG': 'Bulgaria', 'HR': 'Croatia', 'SK': 'Slovakia', 'UA': 'Ukraine',
    'BY': 'Belarus', 'RS': 'Serbia', 'SI': 'Slovenia', 'LT': 'Lithuania',
    'LV': 'Latvia', 'EE': 'Estonia', 'IL': 'Israel', 'MA': 'Morocco',
    'DZ': 'Algeria', 'TN': 'Tunisia', 'KE': 'Kenya', 'ET': 'Ethiopia',
    'GH': 'Ghana', 'TZ': 'Tanzania', 'UG': 'Uganda', 'SN': 'Senegal',
    'CL': 'Chile', 'CO': 'Colombia', 'PE': 'Peru', 'VE': 'Venezuela',
    'EC': 'Ecuador', 'BO': 'Bolivia', 'PY': 'Paraguay', 'UY': 'Uruguay',
    'NZ': 'New Zealand', 'SG': 'Singapore', 'PH': 'Philippines', 'BD': 'Bangladesh',
    'OTHER': 'Other',
}

__all__ = [
    'Meal',
    'MealSelectionRequest',
    'MealSifatGuessRequest',
    'MealLeaderboardEntry',
    'COUNTRY_CODES',
]
