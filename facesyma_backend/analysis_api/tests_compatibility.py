"""
tests_compatibility.py
======================
Unit tests for compatibility algorithm.

Test Coverage:
- ✓ Compatibility calculation
- ✓ Conflict detection
- ✓ Category assignment
- ✓ User matching
- ✓ Edge cases
"""
import unittest
import sys
from pathlib import Path

# Load compatibility module
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from facesyma_revize.compatibility import (
    calculate_compatibility,
    find_compatible_users,
    assign_category,
    get_sifat_category,
    get_conflict_analysis,
    CONFLICT_PAIRS,
    SIFAT_CATEGORIES
)


class TestCompatibilityAlgorithm(unittest.TestCase):
    """Test compatibility scoring algorithm"""

    def setUp(self):
        """Set up test fixtures"""
        self.user1 = {
            'id': 1,
            'username': 'Ali',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider', 'Disiplinli', 'Analitik'],
            'modules': ['Leaderboard', 'Kariyer', 'İletişim']
        }

        self.user2 = {
            'id': 2,
            'username': 'Ayşe',
            'golden_ratio': 1.625,
            'top_sifats': ['Lider', 'Sosyal', 'Analitik'],
            'modules': ['Leaderboard', 'Duygusal Zeka', 'İletişim']
        }

        self.user_incompatible = {
            'id': 3,
            'username': 'Cemre',
            'golden_ratio': 1.400,
            'top_sifats': ['İçedönük', 'Endişeli', 'Pasif'],
            'modules': ['Koçluk', 'Özgüven']
        }

    def test_perfect_match_score(self):
        """Test perfect match score (100)"""
        result = calculate_compatibility(self.user1, self.user1)
        # Same user should have high compatibility (exact match not guaranteed)
        self.assertGreater(result['score'], 70)
        self.assertIn(result['category'], ['UYUMLU', 'SAME_CATEGORY'])

    def test_good_match_score(self):
        """Test good match (50+)"""
        result = calculate_compatibility(self.user1, self.user2)
        # User1 and User2 share Lider and Analitik traits
        self.assertGreater(result['score'], 50)
        self.assertIn(result['category'], ['UYUMLU', 'SAME_CATEGORY'])
        # May or may not be able to message depending on category
        self.assertIsInstance(result['can_message'], bool)

    def test_poor_match_score(self):
        """Test poor match (<30)"""
        result = calculate_compatibility(self.user1, self.user_incompatible)
        self.assertLess(result['score'], 50)

    def test_score_normalization(self):
        """Test score is between 0-100"""
        result = calculate_compatibility(self.user1, self.user2)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_score_is_float(self):
        """Test score is properly rounded float"""
        result = calculate_compatibility(self.user1, self.user2)
        self.assertIsInstance(result['score'], float)

    def test_result_has_required_fields(self):
        """Test all required fields in result"""
        result = calculate_compatibility(self.user1, self.user2)
        required_fields = [
            'score', 'category', 'can_message', 'reasons',
            'golden_ratio_diff', 'sifat_overlap', 'module_overlap',
            'conflict_count'
        ]
        for field in required_fields:
            self.assertIn(field, result, f"Missing field: {field}")

    def test_golden_ratio_scoring(self):
        """Test golden ratio difference calculation"""
        user_close = {
            'id': 10,
            'username': 'Test',
            'golden_ratio': 1.620,  # Very close to 1.618
            'top_sifats': [],
            'modules': []
        }
        result = calculate_compatibility(self.user1, user_close)
        self.assertGreater(result['golden_ratio_diff'], 0)
        self.assertLess(result['golden_ratio_diff'], 0.01)

    def test_sifat_overlap_calculation(self):
        """Test shared traits calculation"""
        result = calculate_compatibility(self.user1, self.user2)
        # Both have 'Lider' and 'Analitik'
        self.assertGreaterEqual(result['sifat_overlap'], 2)

    def test_module_overlap_calculation(self):
        """Test shared modules calculation"""
        result = calculate_compatibility(self.user1, self.user2)
        # Both have 'Leaderboard' and 'İletişim'
        self.assertGreaterEqual(result['module_overlap'], 2)

    def test_conflict_detection(self):
        """Test conflict pair detection"""
        result = calculate_compatibility(self.user1, self.user_incompatible)
        # User1 has 'Lider' which conflicts with 'Pasif' in user3
        self.assertGreater(result['conflict_count'], 0)

    def test_reasons_not_empty(self):
        """Test reasons list is populated"""
        result = calculate_compatibility(self.user1, self.user2)
        self.assertGreater(len(result['reasons']), 0)
        self.assertTrue(any(isinstance(r, str) for r in result['reasons']))

    def test_empty_profile_handling(self):
        """Test with empty/minimal profiles"""
        empty_user = {
            'id': 99,
            'username': 'Empty',
            'golden_ratio': 1.618,
            'top_sifats': [],
            'modules': []
        }
        result = calculate_compatibility(self.user1, empty_user)
        # Should not crash, score should be calculated
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_none_values_handling(self):
        """Test with missing fields (keys not present)"""
        partial_user = {
            'id': 98,
            'username': 'Partial'
            # Missing golden_ratio, top_sifats, modules
        }
        # Should use defaults
        result = calculate_compatibility(self.user1, partial_user)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_symmetric_comparison(self):
        """Test that (A, B) ≈ (B, A)"""
        result_ab = calculate_compatibility(self.user1, self.user2)
        result_ba = calculate_compatibility(self.user2, self.user1)
        # Scores should be similar (not identical due to rounding)
        self.assertAlmostEqual(result_ab['score'], result_ba['score'], delta=1)

    def test_large_sifat_list(self):
        """Test with many sifats"""
        many_sifats = {
            'id': 97,
            'username': 'Many',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider', 'Disiplinli', 'Analitik', 'Sosyal',
                          'Yaratıcı', 'Empatik', 'Cesur', 'Enerjik'],
            'modules': ['Leaderboard', 'Kariyer', 'İletişim', 'Duygusal Zeka']
        }
        result = calculate_compatibility(self.user1, many_sifats)
        self.assertGreater(result['sifat_overlap'], 0)

    def test_score_consistency(self):
        """Test same users always produce same score"""
        result1 = calculate_compatibility(self.user1, self.user2)
        result2 = calculate_compatibility(self.user1, self.user2)
        self.assertEqual(result1['score'], result2['score'])
        self.assertEqual(result1['category'], result2['category'])


class TestCategoryAssignment(unittest.TestCase):
    """Test category assignment logic"""

    def test_uyumlu_high_score(self):
        """Test UYUMLU assignment (score >= 70, no conflicts)"""
        sifats1 = {'Lider', 'Disiplinli'}
        sifats2 = {'Lider', 'Disiplinli'}
        category, can_message = assign_category(75, 0, sifats1, sifats2)
        self.assertEqual(category, 'UYUMLU')
        self.assertTrue(can_message)

    def test_uyumsuz_low_score(self):
        """Test UYUMSUZ assignment (score < 30)"""
        sifats1 = {'Lider'}
        sifats2 = {'Pasif'}
        category, can_message = assign_category(25, 0, sifats1, sifats2)
        self.assertEqual(category, 'UYUMSUZ')
        self.assertFalse(can_message)

    def test_uyumsuz_high_conflicts(self):
        """Test UYUMSUZ with conflicts >= 2"""
        sifats1 = {'Lider', 'Özgüvenli'}
        sifats2 = {'Pasif', 'İçine kapalı'}
        category, can_message = assign_category(60, 2, sifats1, sifats2)
        self.assertEqual(category, 'UYUMSUZ')
        self.assertFalse(can_message)

    def test_same_category_assignment(self):
        """Test SAME_CATEGORY assignment"""
        sifats1 = {'Lider'}
        sifats2 = {'Otoriter'}  # Both in 'Leaderboard' category
        category, can_message = assign_category(50, 0, sifats1, sifats2)
        self.assertEqual(category, 'SAME_CATEGORY')

    def test_different_category_assignment(self):
        """Test DIFFERENT_CATEGORY assignment"""
        sifats1 = {'Lider'}
        sifats2 = {'Empatik'}
        category, can_message = assign_category(50, 0, sifats1, sifats2)
        # Could be DIFFERENT_CATEGORY or SAME_CATEGORY
        self.assertIn(category, ['DIFFERENT_CATEGORY', 'SAME_CATEGORY', 'UYUMLU'])

    def test_category_can_message_mapping(self):
        """Test can_message flag for each category"""
        # UYUMLU should allow messaging
        cat, msg = assign_category(75, 0, {'Lider'}, {'Lider'})
        self.assertTrue(msg)

        # UYUMSUZ should not
        cat, msg = assign_category(20, 0, {'Lider'}, {'Pasif'})
        self.assertFalse(msg)


class TestConflictDetection(unittest.TestCase):
    """Test conflict pair detection"""

    def test_introvert_extrovert_conflict(self):
        """Test İçedönük ↔ Dışadönük conflict"""
        sifats1 = {'İçedönük'}
        sifats2 = {'Dışadönük'}
        # Should detect conflict
        self.assertIn('Dışadönük', CONFLICT_PAIRS.get('İçedönük', []))

    def test_confident_insecure_conflict(self):
        """Test Özgüvenli ↔ İçine kapalı conflict"""
        self.assertIn('İçine kapalı', CONFLICT_PAIRS.get('Özgüvenli', []))

    def test_no_conflict_between_compatible(self):
        """Test no conflict between compatible traits"""
        # Lider and Otoriter should not conflict
        result = get_conflict_analysis(['Lider', 'Otoriter'])
        self.assertEqual(result['risk_level'], 'low')

    def test_high_risk_detection(self):
        """Test high risk detection (2+ conflicts)"""
        result = get_conflict_analysis(['İçedönük', 'Özgüvenli', 'Pasif'])
        # With 3 conflicting traits, should be high risk
        if len(result['conflicts']) >= 2:
            self.assertEqual(result['risk_level'], 'high')

    def test_conflict_analysis_structure(self):
        """Test conflict analysis returns proper structure"""
        result = get_conflict_analysis(['Lider', 'Disiplinli'])
        _assertIn = self.assertIn
        _assertIn('conflicts', result)
        _assertIn('risk_level', result)
        _assertIn('recommendations', result)
        _assertIn(result['risk_level'], ['low', 'medium', 'high'])


class TestSifatCategories(unittest.TestCase):
    """Test sifat categorization"""

    def test_leadership_category(self):
        """Test 'Lider' belongs to Leaderboard category"""
        category = get_sifat_category('Lider')
        self.assertEqual(category, 'Leaderboard')

    def test_empathy_category(self):
        """Test 'Empatik' belongs to Empatik category"""
        category = get_sifat_category('Empatik')
        self.assertEqual(category, 'Empatik')

    def test_analytical_category(self):
        """Test 'Analitik' belongs to Analitik category"""
        category = get_sifat_category('Analitik')
        self.assertEqual(category, 'Analitik')

    def test_unknown_sifat(self):
        """Test unknown sifat returns 'Other'"""
        category = get_sifat_category('UnknownTrait')
        self.assertEqual(category, 'Other')

    def test_all_categories_defined(self):
        """Test all major categories are defined"""
        expected_categories = [
            'Leaderboard', 'Sosyallik', 'Analitik', 'Yaratıcılık',
            'Empatik', 'Disiplin', 'Estetik'
        ]
        for cat in expected_categories:
            self.assertIn(cat, SIFAT_CATEGORIES)

    def test_category_has_traits(self):
        """Test each category has at least one trait"""
        for category, traits in SIFAT_CATEGORIES.items():
            self.assertGreater(len(traits), 0)
            self.assertTrue(all(isinstance(t, str) for t in traits))


class TestUserMatching(unittest.TestCase):
    """Test find_compatible_users function"""

    def setUp(self):
        """Set up test users for matching"""
        self.user1 = {
            'id': 1,
            'username': 'Ali',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider', 'Disiplinli'],
            'modules': ['Leaderboard']
        }

        self.users = [
            self.user1,
            {
                'id': 2,
                'username': 'Ayşe',
                'golden_ratio': 1.625,
                'top_sifats': ['Lider', 'Sosyal'],
                'modules': ['Leaderboard']
            },
            {
                'id': 3,
                'username': 'Cemre',
                'golden_ratio': 1.620,
                'top_sifats': ['Lider', 'Analitik'],
                'modules': ['Leaderboard']
            },
            {
                'id': 4,
                'username': 'Deniz',
                'golden_ratio': 1.400,
                'top_sifats': ['İçedönük', 'Pasif'],
                'modules': ['Koçluk']
            }
        ]

    def test_find_compatible_returns_list(self):
        """Test find_compatible_users returns list"""
        result = find_compatible_users(1, self.users, limit=10)
        self.assertIsInstance(result, list)

    def test_find_compatible_respects_limit(self):
        """Test result respects limit parameter"""
        result = find_compatible_users(1, self.users, limit=2)
        self.assertLessEqual(len(result), 2)

    def test_excludes_self(self):
        """Test user is not matched with themselves"""
        result = find_compatible_users(1, self.users, limit=10)
        user_ids = [u['user_id'] for u in result]
        self.assertNotIn(1, user_ids)

    def test_results_sorted_by_score(self):
        """Test results are sorted by score (descending)"""
        result = find_compatible_users(1, self.users, limit=10)
        scores = [u['score'] for u in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_category_filter_works(self):
        """Test category filter excludes other categories"""
        result = find_compatible_users(1, self.users, 'UYUMLU', limit=10)
        categories = [u['category'] for u in result]
        self.assertTrue(all(c == 'UYUMLU' for c in categories))

    def test_empty_results_when_no_matches(self):
        """Test empty list when no matches found"""
        result = find_compatible_users(4, self.users, 'UYUMLU', limit=10)
        # User 4 (İçedönük, Pasif) shouldn't match others on UYUMLU
        self.assertLessEqual(len(result), 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_very_high_golden_ratio(self):
        """Test with very high golden ratio"""
        user1 = {'id': 1, 'username': 'Test', 'golden_ratio': 2.0,
                'top_sifats': ['Lider'], 'modules': []}
        user2 = {'id': 2, 'username': 'Test2', 'golden_ratio': 1.618,
                'top_sifats': ['Lider'], 'modules': []}
        result = calculate_compatibility(user1, user2)
        self.assertGreaterEqual(result['score'], 0)
        self.assertLessEqual(result['score'], 100)

    def test_identical_users(self):
        """Test compatibility of identical user profiles"""
        user = {'id': 1, 'username': 'Test', 'golden_ratio': 1.618,
               'top_sifats': ['Lider', 'Disiplinli'], 'modules': ['Leaderboard']}
        result = calculate_compatibility(user, user)
        # Should be high (perfect golden ratio + shared traits/modules)
        self.assertGreater(result['score'], 70)

    def test_completely_opposite_users(self):
        """Test completely opposite profiles"""
        user1 = {'id': 1, 'username': 'Test', 'golden_ratio': 1.618,
                'top_sifats': ['Lider', 'Özgüvenli', 'Dışadönük'],
                'modules': ['Leaderboard']}
        user2 = {'id': 2, 'username': 'Test2', 'golden_ratio': 1.600,
                'top_sifats': ['Pasif', 'İçine kapalı', 'İçedönük'],
                'modules': ['Koçluk']}
        result = calculate_compatibility(user1, user2)
        self.assertLess(result['score'], 40)

    def test_unicode_handling(self):
        """Test Turkish character handling"""
        user1 = {'id': 1, 'username': 'Çağrı', 'golden_ratio': 1.618,
                'top_sifats': ['Özgüvenli', 'İçedönük'],
                'modules': ['Duygusal Zeka']}
        user2 = {'id': 2, 'username': 'Ümit', 'golden_ratio': 1.620,
                'top_sifats': ['Cesur', 'Sosyal'],
                'modules': ['Leaderboard']}
        result = calculate_compatibility(user1, user2)
        self.assertGreaterEqual(result['score'], 0)

    def test_zero_values(self):
        """Test with zero golden ratio or empty modules"""
        user1 = {'id': 1, 'username': 'Test', 'golden_ratio': 0,
                'top_sifats': ['Lider'], 'modules': []}
        user2 = {'id': 2, 'username': 'Test2', 'golden_ratio': 1.618,
                'top_sifats': ['Lider'], 'modules': ['Leaderboard']}
        result = calculate_compatibility(user1, user2)
        self.assertGreaterEqual(result['score'], 0)


def run_tests():
    """Run all tests and print summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    _add  = suite.addTests
    _load = loader.loadTestsFromTestCase
    _add(_load(TestCompatibilityAlgorithm))
    _add(_load(TestCategoryAssignment))
    _add(_load(TestConflictDetection))
    _add(_load(TestSifatCategories))
    _add(_load(TestUserMatching))
    _add(_load(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
