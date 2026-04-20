# 🚀 QUICK START - Test Execution

## 3 Terminal Penceresi Aç

### 📍 TERMINAL 1: Django Server

```bash
cd facesyma_backend
python manage.py runserver 0.0.0.0:8000
```

**Beklenen Çıktı:**
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

**✓ Bu terminal açık kalmalı**

---

### 📍 TERMINAL 2: Django Tests

**30 saniye bekle** (Terminal 1'in başlaması için), sonra:

```bash
cd facesyma_backend
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest -v 2
```

**Beklenen Çıktı:**
```
test_01_analytics_dashboard ... ok
test_02_user_growth_metrics ... ok
...
test_42_behavior_segmentation ... ok

Ran 42 tests in X.XXXs

OK
```

**✓ Testler ~5-10 dakika sürer**

---

### 📍 TERMINAL 3: Endpoint Validation

**Terminal 2'de testler çalışırken**, yeni terminal aç:

```bash
cd facesyma-sonn-canim
bash validate_admin_endpoints.sh
```

**Beklenen Çıktı:**
```
╔════════════════════════════════════════════════════════════╗
║         Admin API Endpoint Validation (51 endpoints)        ║
╚════════════════════════════════════════════════════════════╝

✓ [GET] /api/v1/admin/analytics/dashboard/
✓ [GET] /api/v1/admin/analytics/users/growth/
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

**✓ ~1-2 dakika sürer**

---

## ⏱️ Timeline

```
T+0min:   Terminal 1 başla (Django server)
T+30sec:  Terminal 2 başla (Tests)
T+1min:   Terminal 3 başla (Validation)
T+5-10m:  Tests tamamlanır
T+15m:    Tüm validasyonlar tamamlanır
```

---

## ✅ Success Checklist

- [ ] Terminal 1: Django server running (port 8000)
- [ ] Terminal 2: 42 tests passed
- [ ] Terminal 3: 51 endpoints responding
- [ ] No critical errors in any terminal
- [ ] All tests OK

---

## 🎯 Next Step (After Tests Pass)

→ **MONITORING_SETUP.md**

```bash
# Initialize alert rules
python manage.py shell < alert_rules_init.py

# Verify health endpoint
curl http://localhost:8000/api/v1/admin/monitoring/health/
```

---

## 💡 Terminal Setup Tips

**Windows:**
- Cmd.exe veya PowerShell kullan
- 3 pencereyi yan yana yerleştir
- Font size'ı artır (daha rahat izlemek için)

**Mac/Linux:**
- Terminal.app veya iTerm2
- tmux veya screen kullan (isteğe bağlı)
- Font: Courier, size 12+

**All:**
- cd komutundan sonra komutu çalıştırmadan önce Enter'e bas
- Terminal 1'i kapatma (Django server açık kalmalı)

---

**Ready? Start Terminal 1! 🚀**
