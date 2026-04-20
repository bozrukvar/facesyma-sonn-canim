#!/bin/bash
# run_admin_tests.sh
# Admin API Integration Tests çalıştır

echo "================================"
echo "Admin API Integration Tests"
echo "Django Test Runner"
echo "================================"

# Django test runner
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest -v 2

echo ""
echo "Test tamamlandı."
echo "Report:"
echo "- 39+ endpoint test"
echo "- Phase 1: Analytics, Payment, Monitoring (18)"
echo "- Phase 2: Moderation, Content (11)"
echo "- Phase 3: Engagement, Retention (10)"
