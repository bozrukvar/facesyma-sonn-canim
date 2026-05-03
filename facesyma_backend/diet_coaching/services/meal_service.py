"""Meal service — weekly country rotation + MongoDB-backed selections."""
import json
import os
import random
import string
from datetime import datetime, timezone
from typing import List, Tuple

from diet_coaching.models.meal import Meal, Nutrition, Dietary, MealLeaderboardEntry


class MealError(Exception):
    pass


class MealNotFoundError(MealError):
    pass


class InvalidCountryError(MealError):
    pass


# Ordered rotation list — cycles through ISO week number mod len
_WEEKLY_ROTATION = [
    'TR', 'JP', 'IN', 'IT', 'FR', 'DE', 'MX', 'GR',
    'TH', 'MY', 'BR', 'US', 'KR', 'CN', 'AU', 'GB',
    'SA', 'IR', 'NG', 'ZA', 'PH', 'ID', 'PE', 'VN',
]

# Maps country code → JSON filename stem (relative to MEAL_DATA_DIR)
_COUNTRY_FILE_MAP = {
    'TR': 'meals_turkey',
    'US': 'meals_US',
    'GB': 'meals_GB',
    'DE': 'meals_germany',
    'FR': 'meals_france',
    'IT': 'meals_italy',
    'ES': 'meals_es',
    'GR': 'meals_GR',
    'NL': 'meals_NL',
    'BE': 'meals_BE',
    'CH': 'meals_CH',
    'PL': 'meals_pl',
    'JP': 'meals_ja',
    'KR': 'meals_ko',
    'CN': 'meals_zh',
    'IN': 'meals_india',
    'TH': 'meals_th',
    'MY': 'meals_MY',
    'PH': 'meals_PH',
    'ID': 'meals_id',
    'BR': 'meals_BR',
    'MX': 'meals_MX',
    'AU': 'meals_AU',
    'CA': 'meals_CA',
    'ZA': 'meals_ZA',
    'NG': 'meals_NG',
    'KE': 'meals_KE',
    'ET': 'meals_ET',
    'IL': 'meals_IL',
    'IR': 'meals_IR',
    'SA': 'meals_ar',
    'TW': 'meals_TW',
    'PE': 'meals_es_latam',
    'VN': 'meals_vi',
}

# Fallback inline meals (used when data files are unavailable)
_FALLBACK_MEALS = [
    {
        "id": "fallback_001",
        "name_en": "Mixed Salad", "name_tr": "Karışık Salata",
        "description": "Fresh mixed vegetable salad.",
        "nutrition": {"calories": 180, "protein": 4, "carbs": 20, "fat": 8},
        "prep_time_min": 10,
        "dietary": {"omnivore": True, "vegetarian": True, "vegan": True, "gluten_free": True},
        "sifat_appeal": ["saglik_bilinc", "basit_sevici"],
        "season": "year_round", "frequency_weight": 1.0,
    },
    {
        "id": "fallback_002",
        "name_en": "Grilled Chicken", "name_tr": "Izgara Tavuk",
        "description": "Grilled chicken with herbs.",
        "nutrition": {"calories": 280, "protein": 30, "carbs": 5, "fat": 14},
        "prep_time_min": 25,
        "dietary": {"omnivore": True, "vegetarian": False, "vegan": False, "gluten_free": True},
        "sifat_appeal": ["saglik_bilinc", "macera_seven"],
        "season": "year_round", "frequency_weight": 1.0,
    },
    {
        "id": "fallback_003",
        "name_en": "Vegetable Soup", "name_tr": "Sebze Çorbası",
        "description": "Warm vegetable soup.",
        "nutrition": {"calories": 200, "protein": 6, "carbs": 28, "fat": 6},
        "prep_time_min": 20,
        "dietary": {"omnivore": True, "vegetarian": True, "vegan": True, "gluten_free": True},
        "sifat_appeal": ["sevgi_dolu", "basit_sevici"],
        "season": "year_round", "frequency_weight": 1.0,
    },
]


def _gen_id():
    return "ms_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))


def _meal_data_dir() -> str:
    from django.conf import settings
    custom = getattr(settings, 'MEAL_DATA_DIR', '')
    if custom and os.path.isdir(custom):
        return custom
    candidates = [
        '/app/meal_data',
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'facesyma_ai', 'diet_coaching', 'data'),
    ]
    for p in candidates:
        resolved = os.path.realpath(p)
        if os.path.isdir(resolved):
            return resolved
    return ''


def _parse_meal(raw: dict) -> Meal:
    n = raw.get('nutrition') or {}
    d = raw.get('dietary') or {}
    return Meal(
        id=raw.get('id', ''),
        name_en=raw.get('name_en', raw.get('name', '')),
        name_tr=raw.get('name_tr', raw.get('name_en', raw.get('name', ''))),
        description=raw.get('description', ''),
        nutrition=Nutrition(
            calories=int(n.get('calories', 0)),
            protein=int(n.get('protein', 0)),
            carbs=int(n.get('carbs', 0)),
            fat=int(n.get('fat', 0)),
        ),
        dietary=Dietary(
            omnivore=bool(d.get('omnivore', True)),
            vegetarian=bool(d.get('vegetarian', False)),
            vegan=bool(d.get('vegan', False)),
            gluten_free=bool(d.get('gluten_free', False)),
        ),
        prep_time_min=int(raw.get('prep_time_min', 15)),
        sifat_appeal=raw.get('sifat_appeal', []),
        season=raw.get('season', 'year_round'),
        frequency_weight=float(raw.get('frequency_weight', 1.0)),
    )


class MealService:

    @staticmethod
    def _db():
        from admin_api.utils.mongo import _get_db
        return _get_db()

    @staticmethod
    def _get_week_key() -> str:
        now = datetime.now(timezone.utc)
        return now.strftime('%G-W%V')

    @staticmethod
    def get_current_week_country() -> str:
        now = datetime.now(timezone.utc)
        iso_week = int(now.strftime('%V'))
        return _WEEKLY_ROTATION[iso_week % len(_WEEKLY_ROTATION)]

    @staticmethod
    def load_meals(country_code: str) -> List[Meal]:
        data_dir = _meal_data_dir()
        stem = _COUNTRY_FILE_MAP.get(country_code)
        if stem and data_dir:
            path = os.path.join(data_dir, f'{stem}.json')
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        raw_list = json.load(f)
                    return [_parse_meal(r) for r in raw_list]
                except Exception:
                    pass
        return [_parse_meal(r) for r in _FALLBACK_MEALS]

    @staticmethod
    def select_random_meals(meals: List[Meal], count: int = 3) -> List[Meal]:
        if not meals:
            return []
        if len(meals) <= count:
            return meals[:]
        weights = [m.frequency_weight for m in meals]
        chosen = random.choices(meals, weights=weights, k=count * 3)
        seen = set()
        result = []
        for m in chosen:
            if m.id not in seen:
                seen.add(m.id)
                result.append(m)
            if len(result) == count:
                break
        while len(result) < count and len(result) < len(meals):
            for m in meals:
                if m.id not in seen:
                    seen.add(m.id)
                    result.append(m)
                    break
        return result

    @staticmethod
    def select_meal(user_id: int, meal_id: str, country: str) -> Tuple[int, str]:
        db = MealService._db()
        meals = MealService.load_meals(country)
        meal = next((m for m in meals if m.id == meal_id), None)
        if not meal:
            raise MealNotFoundError(meal_id)

        week_key = MealService._get_week_key()
        now = datetime.utcnow()
        trans_id = _gen_id()

        db['meal_selections'].insert_one({
            'trans_id': trans_id,
            'user_id': user_id,
            'meal_id': meal_id,
            'meal_name_en': meal.name_en,
            'country': country,
            'week_key': week_key,
            'selected_at': now.isoformat(),
            'sifat_guess': None,
            'sifat_correct': None,
            'coins_earned': 10,
        })

        from core.services.coin_service import CoinService
        new_balance, _ = CoinService.add_coins(
            user_id=user_id,
            amount=10,
            transaction_type='meal_selection',
            description=f'Meal selected: {meal.name_en}',
        )
        return new_balance, trans_id

    @staticmethod
    def guess_sifat_match(
        user_id: int,
        meal_id: str,
        country: str,
        guess: str,
    ) -> Tuple[bool, int, str]:
        db = MealService._db()
        meals = MealService.load_meals(country)
        meal = next((m for m in meals if m.id == meal_id), None)
        if not meal:
            raise MealNotFoundError(meal_id)

        user = db['appfaceapi_myuser'].find_one({'id': user_id}, {'top_sifats': 1})
        user_sifats = set(user.get('top_sifats', [])) if user else set()
        meal_sifats = set(meal.sifat_appeal)

        has_match = bool(user_sifats & meal_sifats)
        if guess == 'yes':
            is_correct = has_match
        elif guess == 'no':
            is_correct = not has_match
        else:
            is_correct = True

        bonus = 5 if is_correct else 0
        if bonus:
            from core.services.coin_service import CoinService
            CoinService.add_coins(
                user_id=user_id,
                amount=bonus,
                transaction_type='sifat_guess_bonus',
                description=f'Sifat guess correct for {meal_id}',
            )

        db['meal_selections'].update_one(
            {'user_id': user_id, 'meal_id': meal_id, 'week_key': MealService._get_week_key()},
            {'$set': {'sifat_guess': guess, 'sifat_correct': is_correct}},
            upsert=False,
        )

        if is_correct and meal_sifats:
            feedback = f'✓ Correct! This meal appeals to: {", ".join(sorted(meal_sifats))}.'
        elif not is_correct:
            feedback = f'✗ Not quite. This meal appeals to: {", ".join(sorted(meal_sifats)) or "various personalities"}.'
        else:
            feedback = 'Thanks for your honest answer!'

        return is_correct, bonus, feedback

    @staticmethod
    def get_weekly_leaderboard(country: str, limit: int = 100) -> List[MealLeaderboardEntry]:
        db = MealService._db()
        week_key = MealService._get_week_key()
        pipeline = [
            {'$match': {'country': country, 'week_key': week_key}},
            {'$group': {
                '_id': '$user_id',
                'meals_completed': {'$sum': 1},
                'coins_earned': {'$sum': '$coins_earned'},
                'correct_guesses': {'$sum': {'$cond': ['$sifat_correct', 1, 0]}},
                'total_guesses': {'$sum': {'$cond': [{'$ne': ['$sifat_guess', None]}, 1, 0]}},
            }},
            {'$sort': {'coins_earned': -1}},
            {'$limit': limit},
        ]
        agg = list(db['meal_selections'].aggregate(pipeline))
        user_ids = [doc['_id'] for doc in agg]
        users = {
            u['id']: u
            for u in db['appfaceapi_myuser'].find(
                {'id': {'$in': user_ids}}, {'id': 1, 'username': 1, 'avatar': 1}
            )
        }
        entries = []
        for i, doc in enumerate(agg):
            uid = doc['_id']
            u = users.get(uid, {})
            total_g = doc.get('total_guesses', 0)
            accuracy = round(doc.get('correct_guesses', 0) / total_g * 100, 1) if total_g else 0.0
            entries.append(MealLeaderboardEntry(
                rank=i + 1,
                user_id=uid,
                username=u.get('username', f'user_{uid}'),
                avatar=u.get('avatar'),
                meals_completed=doc.get('meals_completed', 0),
                coins_earned=doc.get('coins_earned', 0),
                accuracy_percent=accuracy,
            ))
        return entries

    @staticmethod
    def get_user_meal_history(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[list, int]:
        db = MealService._db()
        col = db['meal_selections']
        total = col.count_documents({'user_id': user_id})
        docs = list(
            col.find({'user_id': user_id}, {'_id': 0})
            .sort('selected_at', -1)
            .skip(offset)
            .limit(limit)
        )
        return docs, total
