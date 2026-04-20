# Test Execution Guide

## 🧪 Integration Tests (42 Test Cases)

### Prerequisites
```bash
cd facesyma_backend
pip install -r requirements.txt
python manage.py migrate
```

### Run All Tests
```bash
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest -v 2
```

### Expected Output
```
test_01_analytics_dashboard (test_admin_api_integration.AdminAPIIntegrationTest) ... ok
test_02_user_growth_metrics (test_admin_api_integration.AdminAPIIntegrationTest) ... ok
test_03_revenue_metrics (test_admin_api_integration.AdminAPIIntegrationTest) ... ok
...
test_42_behavior_segmentation (test_admin_api_integration.AdminAPIIntegrationTest) ... ok

Ran 42 tests in 5.234s
OK
```

### Run Specific Phase
```bash
# Phase 1 only (18 tests)
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest.test_0 -v 2

# Phase 4 only (12 tests)
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest.test_3 -v 2
```

### Endpoint Validation (Quick Check)
```bash
# Django server'ı başlat
python manage.py runserver

# Ayrı bir terminal'de:
bash validate_admin_endpoints.sh
```

Expected:
```
╔════════════════════════════════════════════════════════════╗
║         Admin API Endpoint Validation (39 endpoints)        ║
╚════════════════════════════════════════════════════════════╝

✓ [GET] /api/v1/admin/analytics/dashboard/
✓ [GET] /api/v1/admin/analytics/users/growth/
✓ [GET] /api/v1/admin/analytics/revenue/
...
✓ [GET] /api/v1/admin/retention/segments/

╔════════════════════════════════════════════════════════════╗
║                      TEST SUMMARY                          ║
╠════════════════════════════════════════════════════════════╣
║  Total:      51  │  Success:    51  │  Failed:      0  ║
║                                                            ║
║                  ✓ ALL ENDPOINTS WORKING                 ║
╚════════════════════════════════════════════════════════════╝
```

---

## ✅ Test Checklist

- [ ] Django server running locally
- [ ] MongoDB connected
- [ ] All 42 tests passed
- [ ] All 51 endpoints responding
- [ ] No error logs
- [ ] Response times < 500ms

---

## 🐛 Troubleshooting

### MongoDB Connection Error
```
Error: Server at localhost:27017 refused connection
```
**Fix:** MongoDB Atlas bağlantısını .env'de kontrol et
```
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/facesyma-backend?ssl=true
```

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Fix:** Django sunucusunu farklı port'ta başlat
```bash
python manage.py runserver 8001
```

### Test Timeout
```
TimeoutError: Database operation took too long
```
**Fix:** MongoDB connection timeout artır
```python
# test_admin_api_integration.py'de
MongoClient(..., serverSelectionTimeoutMS=10000)
```

---

## 📊 Test Report Template

Çalıştırdıktan sonra rapor:
```
TESTS RUN: 2026-04-15
============================================

Phase 1 (Analytics, Payment, Monitoring):
  - Status: [PASS/FAIL]
  - Tests: 18/18
  - Duration: XXs

Phase 2 (Moderation, Content):
  - Status: [PASS/FAIL]
  - Tests: 11/11
  - Duration: XXs

Phase 3 (Engagement, Retention):
  - Status: [PASS/FAIL]
  - Tests: 10/10
  - Duration: XXs

Phase 4 (Backup, Logging, Alerts, Reports):
  - Status: [PASS/FAIL]
  - Tests: 12/12
  - Duration: XXs

Endpoint Validation:
  - Total: 51
  - Success: 51
  - Failed: 0

OVERALL: [PASS/FAIL]
```
