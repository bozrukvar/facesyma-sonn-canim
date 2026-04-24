"""
tests_api_endpoints.py
======================
Integration tests for API endpoints.

Test Coverage:
- ✓ Compatibility check endpoint
- ✓ Find compatible users endpoint
- ✓ Compatibility stats endpoint
- ✓ Communities list endpoint
- ✓ Join community endpoint
- ✓ List community members endpoint
"""
import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.http import JsonResponse


class TestCompatibilityCheckEndpoint(TestCase):
    """Test POST /api/v1/compatibility/check/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/compatibility/check/'

    @patch('analysis_api.compatibility_views._get_user_profile')
    @patch('analysis_api.compatibility_views._load_compatibility_module')
    @patch('analysis_api.compatibility_views._get_compatibility_col')
    def test_valid_request(self, mock_col, mock_load, mock_profile):
        """Test valid compatibility check request"""
        # Mock the functions
        mock_calc = MagicMock(return_value={
            'score': 78.5,
            'category': 'UYUMLU',
            'can_message': True,
            'reasons': ['Test reason'],
            'golden_ratio_diff': 0.032,
            'sifat_overlap': 3,
            'module_overlap': 2,
            'conflict_count': 0
        })
        mock_load.return_value = (mock_calc, None)

        user1 = {'id': 1, 'username': 'Ali', 'golden_ratio': 1.618,
                'top_sifats': ['Lider'], 'modules': ['Leaderboard']}
        user2 = {'id': 2, 'username': 'Ayşe', 'golden_ratio': 1.620,
                'top_sifats': ['Lider'], 'modules': ['Leaderboard']}

        mock_profile.side_effect = [user1, user2]
        mock_col.return_value = MagicMock()

        # Make request
        response = self.client.post(
            self.endpoint,
            json.dumps({'user1_id': 1, 'user2_id': 2}),
            content_type='application/json'
        )

        # Verify response
        _aeq = self.assertEqual
        _aeq(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        _aeq(data['data']['score'], 78.5)
        _aeq(data['data']['category'], 'UYUMLU')

    def test_missing_user_ids(self):
        """Test request with missing user IDs"""
        response = self.client.post(
            self.endpoint,
            json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_same_user_error(self):
        """Test error when comparing same user"""
        with patch('analysis_api.compatibility_views._get_user_profile') as mock_profile:
            mock_user = {'id': 1, 'username': 'Ali', 'golden_ratio': 1.618,
                        'top_sifats': ['Lider'], 'modules': ['Leaderboard']}
            mock_profile.return_value = mock_user

            response = self.client.post(
                self.endpoint,
                json.dumps({'user1_id': 1, 'user2_id': 1}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

    def test_user_not_found(self):
        """Test error when user not found"""
        with patch('analysis_api.compatibility_views._get_user_profile') as mock_profile:
            mock_profile.return_value = None

            response = self.client.post(
                self.endpoint,
                json.dumps({'user1_id': 999, 'user2_id': 1}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 404)

    def test_invalid_json(self):
        """Test error with invalid JSON"""
        response = self.client.post(
            self.endpoint,
            'invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class TestFindCompatibleUsersEndpoint(TestCase):
    """Test POST /api/v1/compatibility/find/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/compatibility/find/'

    @patch('analysis_api.compatibility_views._get_user_profile')
    @patch('analysis_api.compatibility_views._load_compatibility_module')
    @patch('analysis_api.compatibility_views._get_db')
    def test_find_compatible_users(self, mock_db, mock_load, mock_profile):
        """Test finding compatible users"""
        user1 = {'id': 1, 'username': 'Ali', 'golden_ratio': 1.618,
                'top_sifats': ['Lider'], 'modules': ['Leaderboard']}

        mock_profile.return_value = user1

        mock_find = MagicMock(return_value=[
            {'user_id': 2, 'username': 'Ayşe', 'score': 78, 'category': 'UYUMLU'},
            {'user_id': 3, 'username': 'Cemre', 'score': 65, 'category': 'SAME_CATEGORY'}
        ])
        mock_load.return_value = (None, mock_find)

        # Mock collection
        mock_users_col = MagicMock()
        mock_users_col.find.return_value.limit.return_value = [user1]
        mock_db.return_value = {'appfaceapi_myuser': mock_users_col}

        response = self.client.post(
            self.endpoint,
            json.dumps({'user_id': 1, 'limit': 10}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)

    def test_missing_user_id(self):
        """Test request with missing user_id"""
        response = self.client.post(
            self.endpoint,
            json.dumps({'limit': 10}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_user_not_found_error(self):
        """Test error when user not found"""
        with patch('analysis_api.compatibility_views._get_user_profile') as mock_profile:
            mock_profile.return_value = None

            response = self.client.post(
                self.endpoint,
                json.dumps({'user_id': 999, 'limit': 10}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 404)


class TestCompatibilityStatsEndpoint(TestCase):
    """Test GET /api/v1/compatibility/stats/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/compatibility/stats/'

    @patch('analysis_api.compatibility_views._get_compatibility_col')
    def test_stats_query(self, mock_col):
        """Test getting compatibility stats"""
        mock_col_instance = MagicMock()
        mock_col_instance.aggregate.return_value = [{
            'total_uyumlu': 42,
            'total_uyumsuz': 15,
            'total_same_category': 28,
            'total_different_category': 8,
            'avg_score': 67.5,
            'highest_score': 95,
            'lowest_score': 15
        }]
        mock_col.return_value = mock_col_instance

        response = self.client.get(self.endpoint, {'user_id': 1})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_uyumlu'], 42)

    def test_missing_user_id(self):
        """Test request with missing user_id"""
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 400)

    def test_invalid_user_id(self):
        """Test error with invalid user_id format"""
        response = self.client.get(self.endpoint, {'user_id': 'invalid'})
        self.assertEqual(response.status_code, 400)

    @patch('analysis_api.compatibility_views._get_compatibility_col')
    def test_empty_stats(self, mock_col):
        """Test stats for user with no compatibility records"""
        mock_col_instance = MagicMock()
        mock_col_instance.aggregate.return_value = []
        mock_col.return_value = mock_col_instance

        response = self.client.get(self.endpoint, {'user_id': 999})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_uyumlu'], 0)


class TestListCommunitiesEndpoint(TestCase):
    """Test GET /api/v1/communities/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/communities/'

    @patch('analysis_api.compatibility_views._get_communities_col')
    def test_list_communities(self, mock_col):
        """Test listing communities"""
        mock_col_instance = MagicMock()
        mock_find = MagicMock()
        mock_find.sort.return_value.limit.return_value = [
            {
                '_id': 'community1',
                'name': 'Leaderboard Topluluğu',
                'type': 'TRAIT',
                'trait_name': 'Lider',
                'member_count': 1245,
                'description': 'Leaders community'
            }
        ]
        mock_col_instance.find.return_value = mock_find
        mock_col.return_value = mock_col_instance

        response = self.client.get(self.endpoint, {'limit': 20})

        _aeq = self.assertEqual
        _aeq(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        _aeq(len(data['data']), 1)
        _aeq(data['data'][0]['name'], 'Leaderboard Topluluğu')

    @patch('analysis_api.compatibility_views._get_communities_col')
    def test_filter_by_type(self, mock_col):
        """Test filtering communities by type"""
        mock_col_instance = MagicMock()
        mock_find = MagicMock()
        mock_find.sort.return_value.limit.return_value = []
        mock_col_instance.find.return_value = mock_find
        mock_col.return_value = mock_col_instance

        response = self.client.get(self.endpoint, {'type': 'TRAIT', 'limit': 20})

        self.assertEqual(response.status_code, 200)
        # Verify find was called with type filter
        call_args = mock_col_instance.find.call_args
        self.assertEqual(call_args[0][0]['type'], 'TRAIT')

    def test_invalid_limit(self):
        """Test error with invalid limit"""
        response = self.client.get(self.endpoint, {'limit': 'invalid'})
        self.assertEqual(response.status_code, 400)


class TestJoinCommunityEndpoint(TestCase):
    """Test POST /api/v1/communities/{id}/join/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/communities/507f1f77bcf86cd799439011/join/'

    @patch('analysis_api.compatibility_views._get_user_profile')
    @patch('analysis_api.compatibility_views._get_communities_col')
    @patch('analysis_api.compatibility_views._get_community_members_col')
    def test_join_community(self, mock_members_col, mock_communities_col, mock_profile):
        """Test joining a community"""
        mock_profile.return_value = {
            'id': 1,
            'username': 'Ali',
            'golden_ratio': 1.618,
            'top_sifats': ['Lider'],
            'modules': ['Leaderboard']
        }

        mock_communities_col.return_value = MagicMock()
        mock_communities_col.return_value.find_one.return_value = {
            '_id': '507f1f77bcf86cd799439011',
            'name': 'Leaderboard Topluluğu'
        }

        mock_members_col.return_value = MagicMock()

        response = self.client.post(
            self.endpoint,
            json.dumps({'user_id': 1}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['membership_status'], 'active')

    def test_missing_community_id(self):
        """Test error when community_id is missing"""
        response = self.client.post(
            '/api/v1/communities//join/',
            json.dumps({'user_id': 1}),
            content_type='application/json'
        )
        # Should get 400 or different endpoint
        self.assertIn(response.status_code, [400, 404])

    def test_missing_user_id(self):
        """Test error with missing user_id"""
        response = self.client.post(
            self.endpoint,
            json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch('analysis_api.compatibility_views._get_communities_col')
    def test_community_not_found(self, mock_col):
        """Test error when community not found"""
        mock_col.return_value.find_one.return_value = None

        response = self.client.post(
            self.endpoint,
            json.dumps({'user_id': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class TestListCommunityMembersEndpoint(TestCase):
    """Test GET /api/v1/communities/{id}/members/"""

    def setUp(self):
        self.client = Client()
        self.endpoint = '/api/v1/communities/507f1f77bcf86cd799439011/members/'

    @patch('analysis_api.compatibility_views._get_community_members_col')
    @patch('analysis_api.compatibility_views._get_db')
    def test_list_members(self, mock_db, mock_members_col):
        """Test listing community members"""
        mock_members_instance = MagicMock()
        mock_find = MagicMock()
        mock_find.sort.return_value.limit.return_value = [
            {
                'user_id': 1,
                'harmony_level': 85,
                'joined_at': 1712000000,
                'is_mod': False
            }
        ]
        mock_members_instance.find.return_value = mock_find
        mock_members_col.return_value = mock_members_instance

        # Mock users collection for enrichment
        mock_users_col = MagicMock()
        mock_users_col.find_one.return_value = {'username': 'Ali'}
        mock_db.return_value = {'appfaceapi_myuser': mock_users_col}

        response = self.client.get(self.endpoint, {'limit': 50})

        _aeq = self.assertEqual
        _aeq(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        _aeq(len(data['data']), 1)
        _aeq(data['data'][0]['harmony_level'], 85)

    @patch('analysis_api.compatibility_views._get_community_members_col')
    def test_sort_by_joined_at(self, mock_col):
        """Test sorting by joined_at"""
        mock_col_instance = MagicMock()
        mock_find = MagicMock()
        mock_find.sort.return_value.limit.return_value = []
        mock_col_instance.find.return_value = mock_find
        mock_col.return_value = mock_col_instance

        response = self.client.get(self.endpoint, {'sort_by': 'joined_at', 'limit': 50})

        self.assertEqual(response.status_code, 200)
        # Verify sort was called with joined_at
        call_args = mock_find.sort.call_args
        self.assertEqual(call_args[0][0], 'joined_at')

    def test_invalid_limit(self):
        """Test error with invalid limit"""
        response = self.client.get(self.endpoint, {'limit': 'invalid'})
        self.assertEqual(response.status_code, 400)


class TestErrorHandling(TestCase):
    """Test error handling across endpoints"""

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        client = Client()
        response = client.post(
            '/api/v1/compatibility/check/',
            '{bad json}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        client = Client()
        response = client.post(
            '/api/v1/compatibility/check/',
            json.dumps({'user1_id': 1}),  # Missing user2_id
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch('analysis_api.compatibility_views._load_compatibility_module')
    @patch('analysis_api.compatibility_views._get_user_profile')
    def test_module_load_error(self, mock_profile, mock_load):
        """Test handling of module load failure"""
        mock_profile.side_effect = [
            {'id': 1, 'username': 'Ali', 'golden_ratio': 1.618, 'top_sifats': [], 'modules': []},
            {'id': 2, 'username': 'Ayşe', 'golden_ratio': 1.620, 'top_sifats': [], 'modules': []}
        ]
        mock_load.return_value = (None, None)  # Load failed

        client = Client()
        response = client.post(
            '/api/v1/compatibility/check/',
            json.dumps({'user1_id': 1, 'user2_id': 2}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 500)


def run_tests():
    """Run all tests and print summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    _add  = suite.addTests
    _load = loader.loadTestsFromTestCase
    _add(_load(TestCompatibilityCheckEndpoint))
    _add(_load(TestFindCompatibleUsersEndpoint))
    _add(_load(TestCompatibilityStatsEndpoint))
    _add(_load(TestListCommunitiesEndpoint))
    _add(_load(TestJoinCommunityEndpoint))
    _add(_load(TestListCommunityMembersEndpoint))
    _add(_load(TestErrorHandling))

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
    import sys
    sys.exit(0 if success else 1)
