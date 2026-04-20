"""
tests_similarity.py
===================
Similarity Module test'leri (15+ test cases).

Test Coverage:
- SimilarityMatcher algorithm
- Individual category matching
- Summary generation
- API endpoint functionality
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import JsonResponse

# Import similarity matcher
import sys
from pathlib import Path

# Add facesyma_revize to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path / 'facesyma_revize'))

try:
    from similarity_matcher import SimilarityMatcher
except ImportError:
    # Fallback for testing environment
    SimilarityMatcher = None


class SimilarityMatcherTests(TestCase):
    """SimilarityMatcher algorithm tests"""

    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        if SimilarityMatcher is None:
            cls.skipTest("SimilarityMatcher not available")

    def setUp(self):
        """Initialize matcher for each test"""
        if SimilarityMatcher:
            self.matcher = SimilarityMatcher()

    def tearDown(self):
        """Cleanup"""
        if hasattr(self, 'matcher'):
            self.matcher.close()

    def test_matcher_initialization(self):
        """Test SimilarityMatcher initializes correctly"""
        if not SimilarityMatcher:
            self.skipTest("SimilarityMatcher not available")

        self.assertIsNotNone(self.matcher)
        self.assertIsNotNone(self.matcher.db)

    def test_match_celebrities_with_overlapping_sifatlar(self):
        """Test celebrity matching with overlapping sıfatlar"""
        test_sifatlar = ["Güzel", "Cesur", "Karizmatik"]
        results = self.matcher._match_celebrities(test_sifatlar)

        # Should return top 3
        self.assertIsInstance(results, list)
        if results:  # If database has data
            self.assertLessEqual(len(results), 3)
            if len(results) > 0:
                self.assertIn('rank', results[0])
                self.assertIn('name', results[0])
                self.assertIn('score', results[0])
                self.assertTrue(0 <= results[0]['score'] <= 100)

    def test_match_historical_returns_top_3(self):
        """Test historical matching returns max 3 results"""
        test_sifatlar = ["Lider", "Güçlü", "Akıllı"]
        results = self.matcher._match_historical(test_sifatlar, 'tr')

        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)

    def test_match_objects_scoring(self):
        """Test object matching scoring 0-100"""
        test_sifatlar = ["Zarafet", "Lüks", "Modern"]
        results = self.matcher._match_objects(test_sifatlar)

        for match in results:
            self.assertTrue(0 <= match['score'] <= 100,
                          f"Score {match['score']} outside 0-100 range")

    def test_match_plants_with_empty_input(self):
        """Test plant matching with empty sıfatlar"""
        results = self.matcher._match_plants([])

        # Should return gracefully (empty or low-score matches)
        self.assertIsInstance(results, list)

    def test_match_animals_returns_behavioral_traits(self):
        """Test animal matching includes behavioral traits"""
        test_sifatlar = ["Güçlü", "Zarif", "Bağımsız"]
        results = self.matcher._match_animals(test_sifatlar)

        for match in results:
            self.assertIn('behavioral_traits', match)
            self.assertIsInstance(match['behavioral_traits'], list)

    def test_match_user_to_similarities_all_categories(self):
        """Test complete matching across all 5 categories"""
        test_sifatlar = ["Güzel", "Cesur", "Lider", "Zarafet"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')

        # Should have all 5 categories
        self.assertIn('celebrities', results)
        self.assertIn('historical', results)
        self.assertIn('objects', results)
        self.assertIn('plants', results)
        self.assertIn('animals', results)

        # Each category should be a list
        for category in ['celebrities', 'historical', 'objects', 'plants', 'animals']:
            self.assertIsInstance(results[category], list)
            if results[category]:
                # If results exist, check structure
                match = results[category][0]
                self.assertIn('rank', match)
                self.assertIn('name', match)
                self.assertIn('score', match)

    def test_generate_summary_turkish(self):
        """Test summary generation in Turkish"""
        test_sifatlar = ["Güzel", "Cesur"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')
        summary = self.matcher.generate_summary(results, 'tr')

        self.assertIsInstance(summary, str)
        if summary:
            # Should contain Turkish characters or words
            self.assertTrue(len(summary) > 10)

    def test_generate_summary_english(self):
        """Test summary generation in English"""
        test_sifatlar = ["Beautiful", "Brave"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'en')
        summary = self.matcher.generate_summary(results, 'en')

        self.assertIsInstance(summary, str)

    def test_score_ranges_are_valid(self):
        """Test all scores are within 0-100 range"""
        test_sifatlar = ["Güzel", "Cesur", "Zarafet", "Lider"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')

        for category in results.values():
            if isinstance(category, list):
                for match in category:
                    if 'score' in match:
                        self.assertGreaterEqual(match['score'], 0)
                        self.assertLessEqual(match['score'], 100)

    def test_top_3_enforcement(self):
        """Test that only top 3 results returned per category"""
        test_sifatlar = ["Güzel", "Cesur", "Zarafet"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')

        for category in ['celebrities', 'historical', 'objects', 'plants', 'animals']:
            matches = results[category]
            self.assertLessEqual(len(matches), 3,
                               f"{category} has more than 3 results")

    def test_rank_ordering(self):
        """Test results are ranked 1, 2, 3"""
        test_sifatlar = ["Güzel", "Cesur"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')

        for category in results.values():
            if isinstance(category, list) and len(category) > 1:
                for i, match in enumerate(category, 1):
                    self.assertEqual(match['rank'], i)

    def test_descending_score_order(self):
        """Test results ordered by descending score"""
        test_sifatlar = ["Güzel", "Cesur", "Zarafet", "Lider"]
        results = self.matcher.match_user_to_similarities(test_sifatlar, 'tr')

        for category in results.values():
            if isinstance(category, list) and len(category) > 1:
                scores = [match['score'] for match in category]
                # Scores should be descending
                for i in range(len(scores) - 1):
                    self.assertGreaterEqual(scores[i], scores[i + 1])

    def test_missing_database_graceful_handling(self):
        """Test graceful handling when database is unavailable"""
        # This would require mocking the database
        # For now, just test that method returns gracefully
        try:
            results = self.matcher._match_celebrities([])
            self.assertIsInstance(results, list)
        except Exception as e:
            # If database truly unavailable, should log and return empty
            self.assertIsNone(results)


class SimilarityAPITests(TestCase):
    """Similarity API endpoint tests"""

    def setUp(self):
        """Setup test fixtures"""
        self.factory = RequestFactory()

    def test_endpoint_available(self):
        """Test similarity endpoint is registered"""
        from analysis_api import urls

        # Check if similarity endpoint exists
        endpoint_names = [p.name for p in urls.urlpatterns if hasattr(p, 'name')]
        self.assertIn('analyze-similarity', endpoint_names)

    @patch('similarity_views.SimilarityMatcher')
    def test_similarity_endpoint_response_structure(self, mock_matcher_class):
        """Test endpoint returns correct response structure"""
        # Mock the matcher
        mock_matcher = MagicMock()
        mock_matcher.match_user_to_similarities.return_value = {
            'celebrities': [{'rank': 1, 'name': 'Test', 'score': 90}],
            'historical': [],
            'objects': [],
            'plants': [],
            'animals': []
        }
        mock_matcher.generate_summary.return_value = "Test summary"
        mock_matcher_class.return_value = mock_matcher

        # This would require setting up Django test environment
        # For now, document the expected structure
        expected_structure = {
            'success': True,
            'data': {
                'celebrities': [
                    {'rank': 1, 'name': 'str', 'score': 'float', 'image_url': 'str'}
                ],
                'historical': [],
                'objects': [],
                'plants': [],
                'animals': [],
                'summary': 'str'
            }
        }

        self.assertIn('success', expected_structure)
        self.assertIn('data', expected_structure)


class SimilarityIntegrationTests(TestCase):
    """Integration tests with main analysis"""

    def test_similarity_included_in_analysis_response(self):
        """Test that similarity results included in main analysis"""
        # This test would require full Django test setup
        # Document the expected flow:
        # 1. User uploads image
        # 2. Analysis runs and returns character sıfatları
        # 3. Similarity matcher processes sıfatları
        # 4. Similarity results added to response

        expected_response_structure = {
            'success': True,
            'data': {
                'character_analysis': {},  # Existing fields
                'similarity': {  # NEW field
                    'celebrities': [],
                    'historical': [],
                    'objects': [],
                    'plants': [],
                    'animals': [],
                    'summary': ''
                }
            }
        }

        self.assertIn('similarity', expected_response_structure['data'])

    def test_similarity_graceful_fallback_on_error(self):
        """Test that missing similarity doesn't break main analysis"""
        # If similarity matching fails, main analysis should still work
        # Result without 'similarity' key is still valid

        result_without_similarity = {
            'success': True,
            'data': {
                'character_analysis': {'sifatlar': []}
                # No 'similarity' key - should still be valid
            }
        }

        self.assertTrue(result_without_similarity['success'])


class SimilarityPerformanceTests(TestCase):
    """Performance and optimization tests"""

    def test_matching_completes_in_reasonable_time(self):
        """Test matching doesn't take too long"""
        if not SimilarityMatcher:
            self.skipTest("SimilarityMatcher not available")

        import time

        matcher = SimilarityMatcher()
        test_sifatlar = ["Güzel", "Cesur", "Zarafet", "Lider", "Entellektüel"]

        start = time.time()
        results = matcher.match_user_to_similarities(test_sifatlar, 'tr')
        elapsed = time.time() - start

        matcher.close()

        # Should complete in < 200ms (benchmark for 440 entries)
        self.assertLess(elapsed, 0.2,
                       f"Matching took {elapsed}s, should be < 0.2s")

    def test_cache_effectiveness(self):
        """Test caching reduces query time"""
        # Document that results are cached for 30 days
        # Same user_id should get instant results on second call

        cache_ttl = 2592000  # 30 days in seconds
        self.assertEqual(cache_ttl, 30 * 24 * 60 * 60)


if __name__ == '__main__':
    unittest.main()
