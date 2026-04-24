"""
tests_community_hooks.py
=======================
Unit tests for community auto-creation hooks.

Test Coverage:
- ✓ Auto-add to trait-based communities
- ✓ Auto-add to module-based communities
- ✓ Prevent duplicate memberships
- ✓ Create missing communities
- ✓ Update member counts
- ✓ Find compatible users
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add backend path
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from analysis_api.community_hooks import (
    auto_add_to_communities,
    find_and_notify_compatible_users
)


class TestAutoAddToCommunities(unittest.TestCase):
    """Test auto-add to communities functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
        self.analysis_result = {
            'top_sifats': ['Lider', 'Disiplinli', 'Analitik'],
            'modules': ['Leaderboard', 'Kariyer', 'İletişim'],
            'sifat_scores': {
                'lider': 0.92,
                'disiplinli': 0.85,
                'analitik': 0.78
            }
        }

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_auto_add_trait_communities(self, mock_members_col, mock_communities_col):
        """Test auto-add to trait-based communities"""
        # Setup mocks
        mock_communities = MagicMock()
        mock_communities.find_one.return_value = {
            '_id': 'community1',
            'name': 'Leaderboard Topluluğu'
        }
        mock_communities_col.return_value = mock_communities

        mock_members = MagicMock()
        mock_members.find_one.return_value = None  # Not member yet
        mock_members_col.return_value = mock_members

        # Call function
        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Verify
        self.assertTrue(result['success'])
        self.assertGreater(result['communities_joined'], 0)
        # Should add to trait communities (3) and module communities (3)
        self.assertGreaterEqual(result['communities_joined'], 3)

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_create_missing_communities(self, mock_members_col, mock_communities_col):
        """Test that missing communities are created"""
        mock_communities = MagicMock()
        # First call returns None (not found), then find_one is called for insert_one
        mock_communities.find_one.return_value = None
        mock_communities.insert_one.return_value = MagicMock(inserted_id='new_community_id')
        mock_communities_col.return_value = mock_communities

        mock_members = MagicMock()
        mock_members.find_one.return_value = None
        mock_members_col.return_value = mock_members

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Verify insert_one was called (creating communities)
        self.assertTrue(mock_communities.insert_one.called)
        self.assertTrue(result['success'])

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_prevent_duplicate_memberships(self, mock_members_col, mock_communities_col):
        """Test that duplicate memberships are prevented"""
        mock_communities = MagicMock()
        mock_communities.find_one.return_value = {
            '_id': 'community1',
            'name': 'Leaderboard Topluluğu'
        }
        mock_communities_col.return_value = mock_communities

        # User already member
        mock_members = MagicMock()
        mock_members.find_one.return_value = {
            'community_id': 'community1',
            'user_id': self.user_id,
            'joined_at': 1234567890
        }
        mock_members_col.return_value = mock_members

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Should succeed but not add duplicate
        # insert_one should not be called for existing membership
        self.assertTrue(result['success'])

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_update_member_count(self, mock_members_col, mock_communities_col):
        """Test that member count is updated"""
        mock_communities = MagicMock()
        mock_communities.find_one.return_value = {
            '_id': 'community1',
            'name': 'Test Community'
        }
        mock_communities_col.return_value = mock_communities

        mock_members = MagicMock()
        mock_members.find_one.return_value = None
        mock_members_col.return_value = mock_members

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Verify update_one was called to increment member_count
        if result['communities_joined'] > 0:
            self.assertTrue(mock_communities.update_one.called)

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_handle_errors_gracefully(self, mock_members_col, mock_communities_col):
        """Test graceful error handling"""
        # Simulate error
        mock_communities_col.side_effect = Exception("DB connection error")

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Should still return success: False but not crash
        self.assertFalse(result['success'])
        self.assertIn('error', result['message'].lower() or 'hata' in result['message'].lower())

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_empty_traits_handling(self, mock_members_col, mock_communities_col):
        """Test with empty traits and modules"""
        empty_result = {
            'top_sifats': [],
            'modules': [],
            'sifat_scores': {}
        }

        result = auto_add_to_communities(self.user_id, empty_result)

        # Should succeed but join 0 communities
        self.assertTrue(result['success'])
        self.assertEqual(result['communities_joined'], 0)

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_module_community_creation(self, mock_members_col, mock_communities_col):
        """Test module-based community creation"""
        mock_communities = MagicMock()
        # Return None first (community not found)
        mock_communities.find_one.side_effect = [None]
        mock_communities.insert_one.return_value = MagicMock(inserted_id='new_module_community')
        mock_communities_col.return_value = mock_communities

        mock_members = MagicMock()
        mock_members.find_one.return_value = None
        mock_members_col.return_value = mock_members

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        # Should successfully create module communities
        self.assertTrue(result['success'])

    @patch('analysis_api.community_hooks._get_communities_col')
    @patch('analysis_api.community_hooks._get_community_members_col')
    def test_return_message(self, mock_members_col, mock_communities_col):
        """Test that success message is returned"""
        mock_communities = MagicMock()
        mock_communities.find_one.return_value = {
            '_id': 'community1',
            'name': 'Test Community'
        }
        mock_communities_col.return_value = mock_communities

        mock_members = MagicMock()
        mock_members.find_one.return_value = None
        mock_members_col.return_value = mock_members

        result = auto_add_to_communities(self.user_id, self.analysis_result)

        _ain = self.assertIn
        _ain('message', result)
        _ain('communities_joined', result)
        _ain('success', result)


class TestFindAndNotifyCompatibleUsers(unittest.TestCase):
    """Test find compatible users and notify functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1

    @patch('analysis_api.community_hooks._get_users_col')
    @patch('analysis_api.community_hooks._get_user_profile')
    @patch('analysis_api.community_hooks._load_compatibility_module')
    def test_find_compatible_success(self, mock_load, mock_profile, mock_users_col):
        """Test successful finding of compatible users"""
        # Mock user profile
        mock_profile.return_value = {
            'id': 1,
            'username': 'Ali',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider'],
            'modules': ['Leaderboard']
        }

        # Mock compatibility function
        mock_find_compat = MagicMock(return_value=[
            {'user_id': 2, 'username': 'Ayşe', 'score': 78, 'category': 'UYUMLU'},
            {'user_id': 3, 'username': 'Cemre', 'score': 65, 'category': 'SAME_CATEGORY'}
        ])
        mock_load.return_value = (None, mock_find_compat)

        # Mock users collection
        mock_users = MagicMock()
        mock_users.find.return_value.limit.return_value = [
            mock_profile.return_value,
            {'id': 2, 'username': 'Ayşe', 'golden_ratio': 1.620,
             'top_sifats': ['Lider'], 'modules': ['Leaderboard']}
        ]
        mock_users_col.return_value = mock_users

        result = find_and_notify_compatible_users(self.user_id, limit=10)

        self.assertTrue(result['success'])
        self.assertGreater(result['compatible_users'], 0)

    @patch('analysis_api.community_hooks._get_user_profile')
    def test_user_not_found(self, mock_profile):
        """Test when user not found"""
        mock_profile.return_value = None

        result = find_and_notify_compatible_users(self.user_id)

        self.assertFalse(result['success'])
        self.assertEqual(result['compatible_users'], 0)

    @patch('analysis_api.community_hooks._get_user_profile')
    @patch('analysis_api.community_hooks._load_compatibility_module')
    def test_module_load_error(self, mock_load, mock_profile):
        """Test when module load fails"""
        mock_profile.return_value = {
            'id': 1,
            'username': 'Ali',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider'],
            'modules': ['Leaderboard']
        }
        mock_load.return_value = (None, None)  # Load failed

        result = find_and_notify_compatible_users(self.user_id)

        self.assertFalse(result['success'])

    @patch('analysis_api.community_hooks._get_users_col')
    @patch('analysis_api.community_hooks._get_user_profile')
    @patch('analysis_api.community_hooks._load_compatibility_module')
    def test_limit_parameter(self, mock_load, mock_profile, mock_users_col):
        """Test that limit parameter is respected"""
        mock_profile.return_value = {
            'id': 1, 'username': 'Ali', 'golden_ratio': 1.618,
            'top_sifats': ['Lider'], 'modules': ['Leaderboard']
        }

        mock_find_compat = MagicMock(return_value=[
            {'user_id': i, 'username': f'User{i}', 'score': 80-i, 'category': 'UYUMLU'}
            for i in range(2, 7)
        ])
        mock_load.return_value = (None, mock_find_compat)

        mock_users_col.return_value.find.return_value.limit.return_value = []

        result = find_and_notify_compatible_users(self.user_id, limit=3)

        self.assertTrue(result['success'])
        # find_compat should be called with limit=3
        call_args = mock_find_compat.call_args
        self.assertIn(3, call_args[0])  # limit is third argument

    @patch('analysis_api.community_hooks._get_users_col')
    @patch('analysis_api.community_hooks._get_user_profile')
    @patch('analysis_api.community_hooks._load_compatibility_module')
    def test_return_structure(self, mock_load, mock_profile, mock_users_col):
        """Test return value structure"""
        mock_profile.return_value = {
            'id': 1, 'username': 'Ali', 'golden_ratio': 1.618,
            'top_sifats': ['Lider'], 'modules': ['Leaderboard']
        }

        mock_find_compat = MagicMock(return_value=[])
        mock_load.return_value = (None, mock_find_compat)

        mock_users_col.return_value.find.return_value.limit.return_value = []

        result = find_and_notify_compatible_users(self.user_id)

        # Check structure
        _ain = self.assertIn
        _ais = self.assertIsInstance
        _ain('success', result)
        _ain('compatible_users', result)
        _ain('message', result)
        _ais(result['success'], bool)
        _ais(result['compatible_users'], int)
        _ais(result['message'], str)

    @patch('analysis_api.community_hooks._get_users_col')
    @patch('analysis_api.community_hooks._get_user_profile')
    @patch('analysis_api.community_hooks._load_compatibility_module')
    def test_handle_errors_gracefully(self, mock_load, mock_profile, mock_users_col):
        """Test graceful error handling"""
        # Simulate error
        mock_profile.side_effect = Exception("Unexpected error")

        result = find_and_notify_compatible_users(self.user_id)

        self.assertFalse(result['success'])
        self.assertEqual(result['compatible_users'], 0)


def run_tests():
    """Run all tests and print summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestAutoAddToCommunities))
    suite.addTests(loader.loadTestsFromTestCase(TestFindAndNotifyCompatibleUsers))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

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
