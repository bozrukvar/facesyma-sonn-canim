"""
similarity_matcher.py
=====================
5 Benzeriniz (Similarity) modülü - matching algoritması.

Özellikler:
- Celebrity matching (face + trait)
- Historical figure matching (trait-based)
- Object/style matching
- Plant/flower matching
- Animal matching (behavior + traits)

Tüm kategoriler: Top 3 sonuç döner.
"""

import heapq
import logging
from operator import itemgetter
from pymongo import MongoClient
from typing import Dict, List, Tuple
import os

log = logging.getLogger(__name__)

_KEY_SCORE = itemgetter(1)
_KEY_SCORE_OVERLAP = lambda x: (x[1], x[2])

_STYLE_MAPPING: dict = {
    'Zarafet': 'Elegant', 'Saflık': 'Minimalist', 'Lüks': 'Luxury',
    'Doğallık': 'Natural', 'Modern': 'Modern', 'Klasik': 'Classic',
    'Profesyonel': 'Professional', 'Yaratıcı': 'Creative',
}

_singleton: 'SimilarityMatcher | None' = None


def get_similarity_matcher() -> 'SimilarityMatcher':
    """Return module-level singleton to avoid per-request MongoClient creation."""
    global _singleton
    if _singleton is None:
        _singleton = SimilarityMatcher()
    return _singleton


class SimilarityMatcher:
    """
    Kullanıcıyı 5 kategoride eşleştir:
    1. Ünlü
    2. Tarihi şahsiyet
    3. Eşya/Stil
    4. Bitki/Çiçek
    5. Hayvan
    """

    def __init__(self, mongo_uri: str = None):
        """Initialize MongoDB connection"""
        if mongo_uri is None:
            mongo_uri = os.environ.get('MONGO_URI', '')

        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client['facesyma-backend']
        except Exception as e:
            log.error(f"MongoDB connection failed: {e}")
            raise
        self._col_cache: dict = {}

    def _load_col(self, col_name: str, limit: int = 5000) -> list:
        """Load and cache a full collection in process memory."""
        _cache = self._col_cache
        if col_name not in _cache:
            _cv = list(self.db[col_name].find({}, {'_id': 0}).limit(limit))
            _cache[col_name] = _cv
            return _cv
        return _cache[col_name]

    def match_user_to_similarities(self, user_sifatlar: List[str], lang: str = 'tr') -> Dict:
        """
        Kullanıcıyı tüm 5 kategoride eşleştir.

        Args:
            user_sifatlar: Kullanıcının sıfatları (list)
            lang: 'tr' or 'en'

        Returns:
            Dict with top 3 matches per category
        """

        results = {
            'celebrities': self._match_celebrities(user_sifatlar),
            'historical': self._match_historical(user_sifatlar, lang),
            'objects': self._match_objects(user_sifatlar),
            'plants': self._match_plants(user_sifatlar),
            'animals': self._match_animals(user_sifatlar)
        }

        return results

    def _match_celebrities(self, user_sifatlar: List[str]) -> List[Dict]:
        """
        Ünlüleri eşleştir (sıfat overlap'ı)

        Returns: List of top 3 matches
        """
        try:
            # Tüm ünlüleri al (process-level cache)
            all_celebrities = self._load_col('similarities_celebrities')

            if not all_celebrities:
                log.warning("No celebrities in database")
                return []

            # Sıfat overlap hesapla
            user_set = set(user_sifatlar)
            matches = []
            for celeb in all_celebrities:
                celeb_set = set(celeb.get('sifatlar', []))
                intersection = len(user_set & celeb_set)
                union = len(user_set | celeb_set)
                similarity = intersection / union if union > 0 else 0
                matches.append((celeb, similarity, intersection))

            # Top 3 döner
            top_3 = heapq.nlargest(3, matches, key=_KEY_SCORE_OVERLAP)

            results = []
            for rank, (celeb, similarity, overlap_count) in enumerate(top_3, 1):
                _cget = celeb.get
                results.append({
                    'rank': rank,
                    'name': _cget('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': _cget('image_url', ''),
                    'sifatlar': _cget('sifatlar', [])[:5],
                    'match_reason': f"{overlap_count} ortak sıfat + kişilik uyumu"
                })

            return results

        except Exception as e:
            log.error(f"Celebrity matching error: {e}")
            return []

    def _match_historical(self, user_sifatlar: List[str], lang: str = 'tr') -> List[Dict]:
        """
        Tarihi şahsiyetleri eşleştir (sıfat overlap'ı)
        """
        try:
            all_figures = self._load_col('similarities_historical')

            if not all_figures:
                log.warning("No historical figures in database")
                return []

            user_set = set(user_sifatlar)
            matches = []
            for figure in all_figures:
                figure_set = set(figure.get('sifatlar', []))
                intersection = len(user_set & figure_set)
                union = len(user_set | figure_set)
                similarity = intersection / union if union > 0 else 0
                matches.append((figure, similarity, intersection))

            top_3 = heapq.nlargest(3, matches, key=_KEY_SCORE_OVERLAP)

            results = []
            for rank, (figure, similarity, overlap_count) in enumerate(top_3, 1):
                _fget = figure.get
                desc_key = f'description_{lang}'
                results.append({
                    'rank': rank,
                    'name': _fget('name', 'Unknown'),
                    'era': _fget('era', ''),
                    'score': round(similarity * 100, 1),
                    'image_url': _fget('image_url', ''),
                    'sifatlar': _fget('sifatlar', [])[:5],
                    'description': _fget(desc_key, _fget('description_en', ''))
                })

            return results

        except Exception as e:
            log.error(f"Historical matching error: {e}")
            return []

    def _match_objects(self, user_sifatlar: List[str]) -> List[Dict]:
        """
        Eşya/Stil'i eşleştir (style traits + elegance)
        """
        try:
            all_objects = self._load_col('similarities_objects')

            if not all_objects:
                log.warning("No objects in database")
                return []

            user_style = [_STYLE_MAPPING.get(s, s) for s in user_sifatlar if s in _STYLE_MAPPING]

            user_style_set = set(user_style)
            matches = []
            for obj in all_objects:
                _oget2 = obj.get
                obj_style_traits = _oget2('style_traits', [])
                overlap = len(user_style_set & set(obj_style_traits))
                style_score = overlap / max(len(user_style), len(obj_style_traits)) if user_style else 0

                # Elegance bonus
                elegance_bonus = (_oget2('elegance_score', 0) / 100) * 0.3

                combined_score = (style_score * 0.7) + elegance_bonus

                matches.append((obj, combined_score))

            top_3 = heapq.nlargest(3, matches, key=_KEY_SCORE)

            results = []
            for rank, (obj, score) in enumerate(top_3, 1):
                _oget = obj.get
                results.append({
                    'rank': rank,
                    'name': _oget('name', 'Unknown'),
                    'score': round(score * 100, 1),
                    'image_url': _oget('image_url', ''),
                    'style_traits': _oget('style_traits', [])[:4],
                    'elegance_score': _oget('elegance_score', 0)
                })

            return results

        except Exception as e:
            log.error(f"Object matching error: {e}")
            return []

    def _match_plants(self, user_sifatlar: List[str]) -> List[Dict]:
        """
        Bitki/Çiçek'i eşleştir (aesthetic + sıfat)
        """
        try:
            all_plants = self._load_col('similarities_plants')

            if not all_plants:
                log.warning("No plants in database")
                return []

            user_set = set(user_sifatlar)
            matches = []
            for plant in all_plants:
                plant_set = set(plant.get('sifatlar', []))
                intersection = len(user_set & plant_set)
                union = len(user_set | plant_set)
                similarity = intersection / union if union > 0 else 0
                matches.append((plant, similarity))

            top_3 = heapq.nlargest(3, matches, key=_KEY_SCORE)

            results = []
            for rank, (plant, similarity) in enumerate(top_3, 1):
                _pget = plant.get
                results.append({
                    'rank': rank,
                    'name': _pget('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': _pget('image_url', ''),
                    'aesthetic_traits': _pget('aesthetic_traits', [])[:4],
                    'color': _pget('color', 'Natural'),
                    'meaning': (_pget('meanings') or ['Nature'])[0]
                })

            return results

        except Exception as e:
            log.error(f"Plant matching error: {e}")
            return []

    def _match_animals(self, user_sifatlar: List[str]) -> List[Dict]:
        """
        Hayvan'ı eşleştir (behavioral + sıfat)
        """
        try:
            all_animals = self._load_col('similarities_animals')

            if not all_animals:
                log.warning("No animals in database")
                return []

            user_set = set(user_sifatlar)
            matches = []
            for animal in all_animals:
                animal_set = set(animal.get('sifatlar', []))
                intersection = len(user_set & animal_set)
                union = len(user_set | animal_set)
                similarity = intersection / union if union > 0 else 0
                matches.append((animal, similarity))

            top_3 = heapq.nlargest(3, matches, key=_KEY_SCORE)

            results = []
            for rank, (animal, similarity) in enumerate(top_3, 1):
                _aget2 = animal.get
                results.append({
                    'rank': rank,
                    'name': _aget2('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': _aget2('image_url', ''),
                    'behavioral_traits': _aget2('behavioral_traits', [])[:4],
                    'habitat': _aget2('habitat', 'Wild')
                })

            return results

        except Exception as e:
            log.error(f"Animal matching error: {e}")
            return []

    def generate_summary(self, results: Dict, lang: str = 'tr') -> str:
        """
        5 kategori sonucundan kısa bir özet yaz.
        """
        try:
            _rget = results.get
            top_celeb = _rget('celebrities', [{}])[0]
            top_animal = _rget('animals', [{}])[0]
            top_plant = _rget('plants', [{}])[0]
            _cn = top_celeb.get('name', 'bilinmeyen' if lang == 'tr' else 'someone')
            _an = top_animal.get('name', 'hayvan' if lang == 'tr' else 'animal')
            _pn = top_plant.get('name', 'çiçek' if lang == 'tr' else 'flower')

            if lang == 'tr':
                return (
                    f"Sen {_cn}'nin güzelliğini taşıyorsun, "
                    f"bir {_an}'nın gücü ve zarafi ile, "
                    f"bir {_pn}'in yaşamı kadar güzelsin! 🌟"
                )
            else:
                return (
                    f"You carry the beauty of {_cn}, "
                    f"with the grace and power of a {_an}, "
                    f"and the life of a {_pn}! 🌟"
                )
        except Exception as e:
            log.error(f"Summary generation error: {e}")
            return ""

    def close(self):
        """Bağlantıyı kapat"""
        if hasattr(self, 'client'):
            self.client.close()


if __name__ == '__main__':
    # Test
    matcher = SimilarityMatcher()

    test_sifatlar = [
        "Güzel", "Cesur", "Karizmatik", "Lider",
        "Entellektüel", "Zarafet", "Duyarlı"
    ]

    results = matcher.match_user_to_similarities(test_sifatlar)

    print("Results:", results)
    print("\nSummary:", matcher.generate_summary(results, 'tr'))

    matcher.close()
