"""
test_admin_api_integration.py
============================
Admin API - Comprehensive Integration Tests

39 endpoint'in tamamını test eder:
- Phase 1: Analytics, Payment, Monitoring (18 endpoints)
- Phase 2: Moderation, Content Management (11 endpoints)
- Phase 3: User Engagement & Retention (10 endpoints)
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from pymongo import MongoClient
from django.conf import settings


class AdminAPIIntegrationTest(TestCase):
    """Admin API Integration Tests - Tüm 39 endpoint"""

    @classmethod
    def setUpClass(cls):
        """Test öncesi MongoDB bağlantı ve admin user oluştur"""
        super().setUpClass()

        # MongoDB client
        cls.mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        cls.db = cls.mongo_client['facesyma-backend']

        # Django client
        cls.client = Client()

        # Admin user oluştur
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

    def setUp(self):
        """Her test öncesi test data oluştur"""
        self.client = Client()

        # MongoDB koleksiyonlarını temizle
        for collection_name in ['users', 'user_subscriptions', 'payment_transactions',
                               'user_reports', 'coaching_content', 'ab_tests',
                               'push_campaigns', 'notification_templates', 'email_campaigns',
                               'user_profiles', 'service_health', 'error_logs']:
            try:
                self.db[collection_name].delete_many({})
            except:
                pass

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: ANALYTICS, PAYMENT, MONITORING
    # ═══════════════════════════════════════════════════════════════════

    def test_01_analytics_dashboard(self):
        """GET /api/v1/admin/analytics/dashboard/ - Dashboard overview"""
        # Test data: Insert sample users
        self.db['users'].insert_many([
            {'user_id': 1, 'created_at': datetime.utcnow(), 'last_active_at': datetime.utcnow()},
            {'user_id': 2, 'created_at': datetime.utcnow(), 'last_active_at': datetime.utcnow()},
        ])

        response = self.client.get('/api/v1/admin/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('total_users', data['data'])
        self.assertIn('active_users', data['data'])

    def test_02_user_growth_metrics(self):
        """GET /admin/analytics/users/growth/ - User growth trends"""
        response = self.client.get('/api/v1/admin/analytics/users/growth/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('growth_data', data['data'])

    def test_03_revenue_metrics(self):
        """GET /admin/analytics/revenue/ - Revenue analysis"""
        response = self.client.get('/api/v1/admin/analytics/revenue/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('mrr', data['data'])
        self.assertIn('arr', data['data'])

    def test_04_community_metrics(self):
        """GET /admin/analytics/communities/ - Community stats"""
        response = self.client.get('/api/v1/admin/analytics/communities/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('total_communities', data['data'])

    def test_05_compatibility_metrics(self):
        """GET /admin/analytics/compatibility/ - Compatibility stats"""
        response = self.client.get('/api/v1/admin/analytics/compatibility/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_06_payment_transactions(self):
        """GET /admin/payments/transactions/ - Payment list"""
        response = self.client.get('/api/v1/admin/payments/transactions/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('transactions', data['data'])

    def test_07_payment_stats(self):
        """GET /admin/payments/stats/ - Payment statistics"""
        response = self.client.get('/api/v1/admin/payments/stats/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_08_payment_settings(self):
        """GET /admin/payments/settings/ - Payment provider config"""
        response = self.client.get('/api/v1/admin/payments/settings/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_09_refund_create(self):
        """POST /admin/payments/refund/ - Create refund"""
        payload = {
            'transaction_id': 'txn_123',
            'amount': 100,
            'reason': 'Customer request'
        }
        response = self.client.post(
            '/api/v1/admin/payments/refund/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_10_webhook_stripe(self):
        """POST /admin/payments/webhook/stripe/ - Stripe webhook"""
        payload = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_123',
                    'amount': 10000,
                    'currency': 'usd'
                }
            }
        }
        response = self.client.post(
            '/api/v1/admin/payments/webhook/stripe/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])  # May fail without real key

    def test_11_webhook_iyzico(self):
        """POST /admin/payments/webhook/iyzico/ - iyzico webhook"""
        payload = {
            'status': 'success',
            'transactionId': 'txn_456'
        }
        response = self.client.post(
            '/api/v1/admin/payments/webhook/iyzico/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_12_health_check(self):
        """GET /admin/monitoring/health/ - Service health"""
        response = self.client.get('/api/v1/admin/monitoring/health/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('services', data['data'])

    def test_13_uptime_metrics(self):
        """GET /admin/monitoring/uptime/ - Uptime tracking"""
        response = self.client.get('/api/v1/admin/monitoring/uptime/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_14_error_rate(self):
        """GET /admin/monitoring/errors/ - Error metrics"""
        response = self.client.get('/api/v1/admin/monitoring/errors/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_15_response_time(self):
        """GET /admin/monitoring/response-time/ - Latency metrics"""
        response = self.client.get('/api/v1/admin/monitoring/response-time/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_16_alert_management(self):
        """GET /admin/monitoring/alerts/ - Alert list"""
        response = self.client.get('/api/v1/admin/monitoring/alerts/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_17_logs_view(self):
        """GET /admin/monitoring/logs/ - System logs"""
        response = self.client.get('/api/v1/admin/monitoring/logs/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: MODERATION & CONTENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════

    def test_18_user_reports_list(self):
        """GET /admin/moderation/reports/ - Report list"""
        response = self.client.get('/api/v1/admin/moderation/reports/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('reports', data['data'])

    def test_19_create_user_report(self):
        """POST /admin/moderation/reports/ - Create report"""
        payload = {
            'reporter_id': 1,
            'reported_user_id': 2,
            'report_type': 'harassment',
            'reason': 'Inappropriate content',
            'description': 'User posted offensive content'
        }
        response = self.client.post(
            '/api/v1/admin/moderation/reports/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_20_review_report(self):
        """POST /admin/moderation/reports/review/ - Review and action"""
        # First create a report
        report = self.db['user_reports'].insert_one({
            'reporter_id': 1,
            'reported_user_id': 2,
            'report_type': 'harassment',
            'status': 'pending'
        })

        payload = {
            'report_id': str(report.inserted_id),
            'action': 'warn',
            'notes': 'First warning'
        }
        response = self.client.post(
            '/api/v1/admin/moderation/reports/review/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_21_content_moderation(self):
        """POST /admin/moderation/content-check/ - Content screening"""
        payload = {
            'content': 'This is a test message',
            'content_type': 'message'
        }
        response = self.client.post(
            '/api/v1/admin/moderation/content-check/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_22_ban_management_list(self):
        """GET /admin/moderation/bans/ - Ban list"""
        response = self.client.get('/api/v1/admin/moderation/bans/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_23_ban_user(self):
        """POST /admin/moderation/bans/ - Ban a user"""
        payload = {
            'user_id': 1,
            'ban_type': 'temporary',
            'duration_days': 7,
            'reason': 'Violation of terms'
        }
        response = self.client.post(
            '/api/v1/admin/moderation/bans/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_24_moderation_stats(self):
        """GET /admin/moderation/stats/ - Moderation statistics"""
        response = self.client.get('/api/v1/admin/moderation/stats/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_25_coaching_content_list(self):
        """GET /admin/content/coaching/ - Coaching content list"""
        response = self.client.get('/api/v1/admin/content/coaching/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_26_create_coaching_content(self):
        """POST /admin/content/coaching/ - Create content"""
        payload = {
            'module': 'kariyer',
            'title': 'Kariyerinde İlerleme',
            'description': 'Nasıl başarılı olabilirsin?',
            'body': 'Detaylı içerik buraya gelir...',
            'languages': ['tr']
        }
        response = self.client.post(
            '/api/v1/admin/content/coaching/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_27_publish_content(self):
        """POST /admin/content/publish/ - Publish or schedule"""
        # First create content
        content = self.db['coaching_content'].insert_one({
            'content_id': 'test_content_1',
            'title': 'Test',
            'status': 'draft'
        })

        payload = {
            'content_id': 'test_content_1',
            'action': 'publish'
        }
        response = self.client.post(
            '/api/v1/admin/content/publish/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_28_translate_content(self):
        """POST /admin/content/translate/ - Add translation"""
        payload = {
            'content_id': 'test_content_1',
            'language': 'en',
            'translation': {
                'title': 'Career Advancement',
                'body': 'How to succeed in your career...'
            }
        }
        response = self.client.post(
            '/api/v1/admin/content/translate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_29_ab_testing_list(self):
        """GET /admin/content/ab-test/ - A/B tests"""
        response = self.client.get('/api/v1/admin/content/ab-test/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_30_create_ab_test(self):
        """POST /admin/content/ab-test/ - Create A/B test"""
        payload = {
            'name': 'Content Variant Test',
            'content_id': 'test_content_1',
            'variant_a': {'title': 'Version A', 'body': 'Body A'},
            'variant_b': {'title': 'Version B', 'body': 'Body B'},
            'duration_days': 7
        }
        response = self.client.post(
            '/api/v1/admin/content/ab-test/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_31_content_analytics(self):
        """GET /admin/content/analytics/ - Content performance"""
        response = self.client.get('/api/v1/admin/content/analytics/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_32_content_templates(self):
        """GET /admin/content/templates/ - Template list"""
        response = self.client.get('/api/v1/admin/content/templates/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: USER ENGAGEMENT & RETENTION
    # ═══════════════════════════════════════════════════════════════════

    def test_33_push_campaigns_list(self):
        """GET /admin/engagement/push-campaigns/ - Campaign list"""
        response = self.client.get('/api/v1/admin/engagement/push-campaigns/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_34_create_push_campaign(self):
        """POST /admin/engagement/push-campaigns/ - Create campaign"""
        payload = {
            'name': 'Holiday Special',
            'title': 'Limited Time Offer',
            'body': 'Get 50% off now!',
            'target_segment': 'all',
            'schedule_type': 'immediate'
        }
        response = self.client.post(
            '/api/v1/admin/engagement/push-campaigns/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 201])

    def test_35_notification_templates(self):
        """GET /admin/engagement/notification-templates/ - Template list"""
        response = self.client.get('/api/v1/admin/engagement/notification-templates/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_36_email_campaigns(self):
        """GET /admin/engagement/email-campaigns/ - Email list"""
        response = self.client.get('/api/v1/admin/engagement/email-campaigns/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_37_campaign_analytics(self):
        """GET /admin/engagement/campaign-analytics/ - Campaign metrics"""
        response = self.client.get('/api/v1/admin/engagement/campaign-analytics/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_38_cohort_analysis(self):
        """GET /admin/retention/cohort-analysis/ - Cohort analysis"""
        response = self.client.get('/api/v1/admin/retention/cohort-analysis/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_39_retention_curve(self):
        """GET /admin/retention/curve/ - Retention trends"""
        response = self.client.get('/api/v1/admin/retention/curve/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_40_churn_prediction(self):
        """GET /admin/retention/churn-prediction/ - Churn risk"""
        response = self.client.get('/api/v1/admin/retention/churn-prediction/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_41_user_funnel(self):
        """GET /admin/retention/funnel/ - Conversion funnel"""
        response = self.client.get('/api/v1/admin/retention/funnel/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_42_behavior_segmentation(self):
        """GET /admin/retention/segments/ - User segments"""
        response = self.client.get('/api/v1/admin/retention/segments/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
