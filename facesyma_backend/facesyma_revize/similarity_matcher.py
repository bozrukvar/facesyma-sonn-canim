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

import logging
from pymongo import MongoClient
from typing import Dict, List, Tuple
import os

log = logging.getLogger(__name__)


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
            mongo_uri = os.environ.get(
                'MONGO_URI',
                'mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE'
            )

        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client['facesyma-backend']
        except Exception as e:
            log.error(f"MongoDB connection failed: {e}")
            raise

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
            celebrities_col = self.db['similarities_celebrities']

            # Tüm ünlüleri al
            all_celebrities = list(celebrities_col.find({}, {'_id': 0}))

            if not all_celebrities:
                log.warning("No celebrities in database")
                return []

            # Sıfat overlap hesapla
            matches = []
            for celeb in all_celebrities:
                celeb_sifatlar = celeb.get('sifatlar', [])

                # Jaccard similarity
                intersection = len(set(user_sifatlar) & set(celeb_sifatlar))
                union = len(set(user_sifatlar) | set(celeb_sifatlar))
                similarity = intersection / union if union > 0 else 0

                matches.append((celeb, similarity, intersection))

            # Top 3 döner
            top_3 = sorted(matches, key=lambda x: (x[1], x[2]), reverse=True)[:3]

            results = []
            for rank, (celeb, similarity, overlap_count) in enumerate(top_3, 1):
                results.append({
                    'rank': rank,
                    'name': celeb.get('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': celeb.get('image_url', ''),
                    'sifatlar': celeb.get('sifatlar', [])[:5],
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
            historical_col = self.db['similarities_historical']

            all_figures = list(historical_col.find({}, {'_id': 0}))

            if not all_figures:
                log.warning("No historical figures in database")
                return []

            matches = []
            for figure in all_figures:
                figure_sifatlar = figure.get('sifatlar', [])

                intersection = len(set(user_sifatlar) & set(figure_sifatlar))
                union = len(set(user_sifatlar) | set(figure_sifatlar))
                similarity = intersection / union if union > 0 else 0

                matches.append((figure, similarity, intersection))

            top_3 = sorted(matches, key=lambda x: (x[1], x[2]), reverse=True)[:3]

            results = []
            for rank, (figure, similarity, overlap_count) in enumerate(top_3, 1):
                desc_key = f'description_{lang}'
                results.append({
                    'rank': rank,
                    'name': figure.get('name', 'Unknown'),
                    'era': figure.get('era', ''),
                    'score': round(similarity * 100, 1),
                    'image_url': figure.get('image_url', ''),
                    'sifatlar': figure.get('sifatlar', [])[:5],
                    'description': figure.get(desc_key, figure.get('description_en', ''))
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
            objects_col = self.db['similarities_objects']

            all_objects = list(objects_col.find({}, {'_id': 0}))

            if not all_objects:
                log.warning("No objects in database")
                return []

            # Style mapping: sıfatları style traits'e çevir
            style_mapping = {
                'Zarafet': 'Elegant',
                'Saflık': 'Minimalist',
                'Lüks': 'Luxury',
                'Doğallık': 'Natural',
                'Modern': 'Modern',
                'Klasik': 'Classic',
                'Profesyonel': 'Professional',
                'Yaratıcı': 'Creative'
            }

            user_style = [style_mapping.get(s, s) for s in user_sifatlar if s in style_mapping]

            matches = []
            for obj in all_objects:
                obj_style_traits = obj.get('style_traits', [])

                overlap = len(set(user_style) & set(obj_style_traits))
                style_score = overlap / max(len(user_style), len(obj_style_traits)) if user_style else 0

                # Elegance bonus
                elegance_bonus = (obj.get('elegance_score', 0) / 100) * 0.3

                combined_score = (style_score * 0.7) + elegance_bonus

                matches.append((obj, combined_score))

            top_3 = sorted(matches, key=lambda x: x[1], reverse=True)[:3]

            results = []
            for rank, (obj, score) in enumerate(top_3, 1):
                results.append({
                    'rank': rank,
                    'name': obj.get('name', 'Unknown'),
                    'score': round(score * 100, 1),
                    'image_url': obj.get('image_url', ''),
                    'style_traits': obj.get('style_traits', [])[:4],
                    'elegance_score': obj.get('elegance_score', 0)
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
            plants_col = self.db['similarities_plants']

            all_plants = list(plants_col.find({}, {'_id': 0}))

            if not all_plants:
                log.warning("No plants in database")
                return []

            matches = []
            for plant in all_plants:
                plant_sifatlar = plant.get('sifatlar', [])

                intersection = len(set(user_sifatlar) & set(plant_sifatlar))
                union = len(set(user_sifatlar) | set(plant_sifatlar))
                similarity = intersection / union if union > 0 else 0

                matches.append((plant, similarity))

            top_3 = sorted(matches, key=lambda x: x[1], reverse=True)[:3]

            results = []
            for rank, (plant, similarity) in enumerate(top_3, 1):
                results.append({
                    'rank': rank,
                    'name': plant.get('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': plant.get('image_url', ''),
                    'aesthetic_traits': plant.get('aesthetic_traits', [])[:4],
                    'color': plant.get('color', 'Natural'),
                    'meaning': plant.get('meanings', ['Beauty'])[0] if plant.get('meanings') else 'Nature'
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
            animals_col = self.db['similarities_animals']

            all_animals = list(animals_col.find({}, {'_id': 0}))

            if not all_animals:
                log.warning("No animals in database")
                return []

            matches = []
            for animal in all_animals:
                animal_sifatlar = animal.get('sifatlar', [])

                intersection = len(set(user_sifatlar) & set(animal_sifatlar))
                union = len(set(user_sifatlar) | set(animal_sifatlar))
                similarity = intersection / union if union > 0 else 0

                matches.append((animal, similarity))

            top_3 = sorted(matches, key=lambda x: x[1], reverse=True)[:3]

            results = []
            for rank, (animal, similarity) in enumerate(top_3, 1):
                results.append({
                    'rank': rank,
                    'name': animal.get('name', 'Unknown'),
                    'score': round(similarity * 100, 1),
                    'image_url': animal.get('image_url', ''),
                    'behavioral_traits': animal.get('behavioral_traits', [])[:4],
                    'habitat': animal.get('habitat', 'Wild')
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
            top_celeb = results.get('celebrities', [{}])[0]
            top_animal = results.get('animals', [{}])[0]
            top_plant = results.get('plants', [{}])[0]

            if lang == 'tr':
                return (
                    f"Sen {top_celeb.get('name', 'bilinmeyen')}'nin güzelliğini taşıyorsun, "
                    f"bir {top_animal.get('name', 'hayvan')}'nın gücü ve zarafi ile, "
                    f"bir {top_plant.get('name', 'çiçek')}'in yaşamı kadar güzelsin! 🌟"
                )
            else:
                return (
                    f"You carry the beauty of {top_celeb.get('name', 'someone')}, "
                    f"with the grace and power of a {top_animal.get('name', 'animal')}, "
                    f"and the life of a {top_plant.get('name', 'flower')}! 🌟"
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
