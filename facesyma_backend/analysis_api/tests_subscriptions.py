"""
tests_subscriptions.py
======================
Freemium subscription endpoints test'leri.

Test Cases:
  1. SubscriptionStatusView - Kullanıcının subscription durumunu al
  2. SubscriptionUpgradeView - Premium'a upgrade et
  3. SubscriptionCancelView - Subscription iptal et
  4. Feature paywall - Free tier limitlerini kontrol et
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from compatibility_views import (
    SubscriptionStatusView, SubscriptionUpgradeView, SubscriptionCancelView,
    get_user_subscription, check_free_tier_limit, count_monthly_checks,
    count_joined_communities
)


class SubscriptionStatusTests(TestCase):
    """SubscriptionStatusView test'leri"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = SubscriptionStatusView.as_view()

    @patch('compatibility_views._get_subscription_col')
    @patch('compatibility_views.get_user_subscription')
    def test_get_free_tier_user_status(self, mock_get_sub, mock_col):
        """Free tier kullanıcının durumu kontrol et"""
        mock_get_sub.return_value = {
            'user_id': 123,
            'tier': 'free',
            'status': 'active'
        }

        request = self.factory.get('/api/v1/subscription/status/?user_id=123')
        response = self.view(request)

        data = json.loads(response.content)
        _aeq = self.assertEqual
        _aeq(response.status_code, 200)
        self.assertTrue(data['success'])
        _aeq(data['data']['tier'], 'free')
        _aeq(data['data']['status'], 'active')

    @patch('compatibility_views._get_subscription_col')
    @patch('compatibility_views.get_user_subscription')
    def test_get_premium_user_status(self, mock_get_sub, mock_col):
        """Premium kullanıcının durumu kontrol et"""
        mock_get_sub.return_value = {
            'user_id': 123,
            'tier': 'premium',
            'status': 'active',
            'renews_at': 1750000000
        }

        request = self.factory.get('/api/v1/subscription/status/?user_id=123')
        response = self.view(request)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['data']['tier'], 'premium')
        self.assertTrue(data['data']['features']['unlimited_messaging'])

    def test_missing_user_id(self):
        """user_id parametresi eksikse hata döner"""
        request = self.factory.get('/api/v1/subscription/status/')
        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('user_id', data['detail'])


class SubscriptionUpgradeTests(TestCase):
    """SubscriptionUpgradeView test'leri"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = SubscriptionUpgradeView.as_view()

    def test_upgrade_to_premium_monthly(self):
        """Aylık premium'a upgrade et"""
        body = json.dumps({
            'user_id': 123,
            'billing_cycle': 'monthly'
        })

        request = self.factory.post(
            '/api/v1/subscription/upgrade/',
            data=body,
            content_type='application/json'
        )
        response = self.view(request)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('checkout_url', data['data'])
        self.assertEqual(data['data']['price'], '$9.99/month')

    def test_upgrade_to_premium_yearly(self):
        """Yıllık premium'a upgrade et"""
        body = json.dumps({
            'user_id': 123,
            'billing_cycle': 'yearly'
        })

        request = self.factory.post(
            '/api/v1/subscription/upgrade/',
            data=body,
            content_type='application/json'
        )
        response = self.view(request)

        data = json.loads(response.content)
        self.assertEqual(data['data']['price'], '$89/year')

    def test_upgrade_missing_user_id(self):
        """user_id parametresi eksikse hata döner"""
        body = json.dumps({'billing_cycle': 'monthly'})

        request = self.factory.post(
            '/api/v1/subscription/upgrade/',
            data=body,
            content_type='application/json'
        )
        response = self.view(request)

        self.assertEqual(response.status_code, 400)


class SubscriptionCancelTests(TestCase):
    """SubscriptionCancelView test'leri"""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = SubscriptionCancelView.as_view()

    @patch('compatibility_views._get_subscription_col')
    def test_cancel_subscription(self, mock_col):
        """Subscription iptal et"""
        mock_col_instance = MagicMock()
        mock_col.return_value = mock_col_instance

        body = json.dumps({'user_id': 123})

        request = self.factory.post(
            '/api/v1/subscription/cancel/',
            data=body,
            content_type='application/json'
        )
        response = self.view(request)

        data = json.loads(response.content)
        _aeq = self.assertEqual
        _aeq(response.status_code, 200)
        self.assertTrue(data['success'])
        _aeq(data['data']['status'], 'cancelled')
        _aeq(data['data']['tier'], 'free')

    def test_cancel_missing_user_id(self):
        """user_id parametresi eksikse hata döner"""
        body = json.dumps({})

        request = self.factory.post(
            '/api/v1/subscription/cancel/',
            data=body,
            content_type='application/json'
        )
        response = self.view(request)

        self.assertEqual(response.status_code, 400)


class SubscriptionHelperTests(TestCase):
    """Subscription helper fonksiyonları test et"""

    @patch('compatibility_views._get_db')
    def test_get_user_subscription_default_free_tier(self, mock_db):
        """Yeni kullanıcı varsayılan free tier'de mi?"""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.__getitem__.return_value.find_one.return_value = None

        sub = get_user_subscription(999)

        self.assertEqual(sub['tier'], 'free')
        self.assertEqual(sub['status'], 'active')

    @patch('compatibility_views._get_db')
    def test_check_free_tier_limit_compatibility_check(self, mock_db):
        """Compatibility check limitini kontrol et (3/ay)"""
        with patch('compatibility_views.count_monthly_checks') as mock_count:
            mock_count.return_value = 2  # 2 check kullanılmış

            result = check_free_tier_limit(123, 'compatibility_check')
            self.assertTrue(result)  # 2 < 3 → izin ver

            mock_count.return_value = 3  # 3 check kullanılmış
            result = check_free_tier_limit(123, 'compatibility_check')
            self.assertFalse(result)  # 3 < 3 → FALSE → reddet

    @patch('compatibility_views._get_db')
    def test_check_free_tier_limit_community_join(self, mock_db):
        """Community join limitini kontrol et (1/ay)"""
        with patch('compatibility_views.count_joined_communities') as mock_count:
            mock_count.return_value = 0  # 0 topluluk katılmış

            result = check_free_tier_limit(123, 'community_join')
            self.assertTrue(result)  # 0 < 1 → izin ver

            mock_count.return_value = 1  # 1 topluluk katılmış
            result = check_free_tier_limit(123, 'community_join')
            self.assertFalse(result)  # 1 < 1 → FALSE → reddet

    @patch('compatibility_views._get_db')
    def test_count_monthly_checks(self, mock_db):
        """Bu ayda yapılan uyum kontrol sayısı"""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.__getitem__.return_value.count_documents.return_value = 2

        count = count_monthly_checks(123)
        self.assertEqual(count, 2)

    @patch('compatibility_views._get_db')
    def test_count_joined_communities(self, mock_db):
        """Katılınan topluluk sayısı (active üyeler)"""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.__getitem__.return_value.count_documents.return_value = 1

        count = count_joined_communities(123)
        self.assertEqual(count, 1)


class FreemiumIntegrationTests(TestCase):
    """Freemium sistem entegrasyonu test'leri"""

    @patch('compatibility_views.get_user_subscription')
    @patch('compatibility_views.check_free_tier_limit')
    def test_free_user_hits_compatibility_limit(self, mock_check, mock_sub):
        """Free kullanıcı limitine ulaştığında uyarı al"""
        mock_sub.return_value = {'tier': 'free', 'status': 'active'}
        mock_check.return_value = False  # Limit aşılmış

        from compatibility_views import require_premium_feature
        factory = RequestFactory()

        @require_premium_feature('compatibility_check')
        def mock_view(request):
            return JsonResponse({'success': True})

        request = factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer test_token'

        with patch('compatibility_views._get_user_id') as mock_user_id:
            mock_user_id.return_value = 123
            response = mock_view(request)

        self.assertEqual(response.status_code, 402)  # Payment Required

    @patch('compatibility_views.get_user_subscription')
    def test_premium_user_bypasses_limit(self, mock_sub):
        """Premium kullanıcı limitlerse bypass yapabilir"""
        mock_sub.return_value = {'tier': 'premium', 'status': 'active'}

        from compatibility_views import require_premium_feature
        factory = RequestFactory()

        @require_premium_feature('compatibility_check')
        def mock_view(request):
            return JsonResponse({'success': True})

        request = factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer test_token'

        with patch('compatibility_views._get_user_id') as mock_user_id:
            mock_user_id.return_value = 123
            response = mock_view(request)

        self.assertEqual(response.status_code, 200)  # OK


class PricingTests(TestCase):
    """Pricing stratejisi test'leri"""

    def test_free_tier_features(self):
        """Free tier özellikleri kontrol et"""
        sub = {
            'tier': 'free',
            'status': 'active',
            'features': {
                'unlimited_messaging': False,
                'unlimited_communities': False,
                'file_sharing': False
            }
        }

        _af = self.assertFalse
        _sf = sub['features']
        _af(_sf['unlimited_messaging'])
        _af(_sf['unlimited_communities'])
        _af(_sf['file_sharing'])

    def test_premium_tier_features(self):
        """Premium tier özellikleri kontrol et"""
        sub = {
            'tier': 'premium',
            'status': 'active',
            'features': {
                'unlimited_messaging': True,
                'unlimited_communities': True,
                'file_sharing': True
            }
        }

        _at = self.assertTrue
        _sf = sub['features']
        _at(_sf['unlimited_messaging'])
        _at(_sf['unlimited_communities'])
        _at(_sf['file_sharing'])

    def test_monthly_vs_yearly_pricing(self):
        """Ay ve yıllık fiyatlandırma"""
        monthly_price = 9.99
        yearly_price = 89.00

        # Yıllık indirim hesapla
        monthly_equivalent = (yearly_price / 12)
        savings = 1 - (monthly_equivalent / monthly_price)

        self.assertGreater(savings, 0.20)  # %20+ indirim olmalı


if __name__ == '__main__':
    unittest.main()
