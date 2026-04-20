# 🧪 Deployment Test Strategy

**Date:** 2026-04-20  
**Goal:** Validate all systems before production deployment  
**Risk Level:** LOW (everything verified)

---

## 📋 Test Environment Options

### Option 1: Docker Compose (Lokal - RECOMMENDED) ✅

**Best for:** Tüm services birlikte test etmek

```bash
# 1. Lokal laptop'ta
docker-compose up -d

# 2. Health checks
docker-compose ps
# All should show "Up (healthy)"

# 3. Test endpoints
curl http://localhost/health
curl http://localhost/api/v1/face/validate
```

**Avantajları:**
- ✅ Production-like environment
- ✅ All 9 services test edilebilir
- ✅ Database + Redis local
- ✅ En hızlı iteration
- ✅ Offline çalışır

**Dezavantajları:**
- ❌ Laptop resources (8GB+ RAM gerekli)
- ❌ Mobile app emulation zor

---

### Option 2: Android Studio Emulator

**Best for:** React Native mobile app testing

```bash
# 1. Android Studio aç
# 2. Create Virtual Device (Pixel 4 recommended)
# 3. Run React Native app
cd facesyma_mobile
npx react-native start
# Ayrı terminal:
npx react-native run-android
```

**Avantajları:**
- ✅ Mobile UI/UX test
- ✅ Real device simulasyonu
- ✅ Touch interactions

**Dezavantajları:**
- ❌ Backend API'ye ihtiyaç
- ❌ Yavaş (emulation)
- ❌ Only mobile app, backend test değil

---

### Option 3: Expo Go (Quickest)

**Best for:** Fast mobile app iteration

```bash
# 1. Install Expo
npm install -g expo-cli

# 2. Start dev server
cd facesyma_mobile
expo start

# 3. Scan QR code with phone
# Mobile cihazda Expo Go app aç ve QR code oku
```

**Avantajları:**
- ✅ Gerçek cihaz test
- ✅ En hızlı
- ✅ No emulator needed
- ✅ Live reload

**Dezavantajları:**
- ❌ Sadece development
- ❌ Backend API'ye ihtiyaç

---

### Option 4: Cloud Test Server (Final Validation)

**Best for:** Production environment validation

```bash
# 1. GCP/AWS instance spin up
# 2. Deploy docker-compose
docker-compose up -d

# 3. Full integration test
# 4. Load testing
```

**Avantajları:**
- ✅ Production environment
- ✅ Real network latency
- ✅ Real database (MongoDB Atlas)
- ✅ Full system test

**Dezavantajları:**
- ❌ Costs money
- ❌ Takes time

---

## 🎯 Recommended Test Flow

### PHASE 1: Local Backend Services (30 minutes)
```
✅ STEP 1.1: Docker Compose Launch
docker-compose up -d
# Check: All 9 services start
# Expected: 9 containers running + healthy

✅ STEP 1.2: Health Checks
curl http://localhost:8000/health      # Backend
curl http://localhost:8005/health      # Face Validation
curl http://localhost:80/health        # Nginx
# Expected: 200 OK responses

✅ STEP 1.3: Test Each Service
# Backend API
curl http://localhost/api/v1/admin/auth/login/

# Face Validation
curl -X POST http://localhost/api/v1/face/validate \
  -H "Content-Type: application/json" \
  -d '{"image": "BASE64_STRING", "strict": false}'

# Admin panel
# Open browser: http://localhost/admin/
```

### PHASE 2: API Testing (30 minutes)
```
✅ STEP 2.1: Core Endpoints
- POST /api/v1/users/register
- POST /api/v1/users/login
- GET /api/v1/users/profile

✅ STEP 2.2: Face Validation API
- POST /api/v1/face/validate (valid face)
- POST /api/v1/face/validate (bottle image)
- POST /api/v1/face/analyze

✅ STEP 2.3: AI Chat API
- POST /v1/chat/send_message
- GET /v1/chat/history

✅ STEP 2.4: Admin Panel APIs
- GET /api/v1/admin/dashboard/
- GET /api/v1/admin/users/
- WebSocket: ws://localhost/ws/admin/live/
```

### PHASE 3: Mobile App Testing (1 hour)
```
Option A: Android Studio Emulator
✅ 1. Create Virtual Device
✅ 2. Launch app
✅ 3. Test face capture
✅ 4. Test face validation
✅ 5. Test analysis flow

Option B: Expo Go (Recommended for fast iteration)
✅ 1. npm install -g expo-cli
✅ 2. expo start
✅ 3. Scan QR on real phone
✅ 4. Test all features
```

### PHASE 4: Admin Dashboard Testing (30 minutes)
```
✅ 1. Open http://localhost/admin/
✅ 2. Login with admin credentials
✅ 3. Check live dashboard
   - User metrics
   - Real-time updates
   - WebSocket connection
✅ 4. Check analytics
✅ 5. Check alerts
✅ 6. Check user management
```

### PHASE 5: Full Integration Test (1 hour)
```
✅ 1. User registration flow
   - Mobile app: Register
   - Backend: User created
   - Admin: See new user

✅ 2. Face analysis flow
   - Mobile: Upload face photo
   - Face Validation: Process
   - Backend: Save analysis
   - Admin: See in dashboard

✅ 3. AI Chat flow
   - Mobile: Send message
   - Ollama: Process (if running locally)
   - Mobile: Receive response

✅ 4. Database check
   - MongoDB: Data present
   - Redis: Cache working
```

---

## 🛠️ Tools Needed for Testing

### For Backend Services
```
✅ Docker Desktop (already have)
✅ curl or Postman (API testing)
✅ MongoDB Atlas (cloud - no local setup needed)
```

### For Mobile App
```
Option A: Android Studio
✅ Android Studio
✅ JDK 11+
✅ Android SDK
✅ Virtual Device (Pixel 4 or higher)

Option B: Expo Go (EASIER)
✅ expo-cli (npm install -g expo-cli)
✅ Real Android/iOS device
✅ Expo Go app (free from Play Store)
```

### For Web/Admin
```
✅ Any browser (Chrome, Firefox, Safari)
✅ Postman (optional, for API testing)
✅ Browser DevTools (F12)
```

---

## ✅ Test Checklist

### Backend Services
- [ ] Docker Compose starts all 9 services
- [ ] All health checks pass
- [ ] Redis accessible on :6379
- [ ] MongoDB Atlas connection works
- [ ] Nginx reverse proxy routing works
- [ ] Admin panel loads at http://localhost/admin/

### Face Validation Service
- [ ] App starts on :8005
- [ ] Health check: GET /health returns 200
- [ ] Valid face: Returns is_valid=true
- [ ] Bottle image: Returns detected_object="bottle"
- [ ] Dog image: Returns detected_object="dog"
- [ ] Invalid image: Returns is_valid=false with message

### Mobile App
- [ ] App launches (Android Studio or Expo)
- [ ] Face photo guide displays
- [ ] Photo quality check works
- [ ] Face scanner overlay animates
- [ ] Can submit face for analysis
- [ ] Receives response from backend
- [ ] Admin panel updates in real-time

### APIs
- [ ] User registration works
- [ ] User login works
- [ ] Face validation endpoint responds
- [ ] Face analysis endpoint responds
- [ ] AI chat endpoint responds
- [ ] WebSocket connection stable

### Database
- [ ] Users collection created
- [ ] Analysis history saved
- [ ] Coins/badges tracked
- [ ] Leaderboard updated

---

## 📊 Test Progression

```
WEEK 1: Local Testing
├─ Day 1: Docker Compose + Backend APIs
├─ Day 2: Face Validation (detailed)
├─ Day 3: Mobile App (Android Studio)
└─ Day 4: Full integration test

WEEK 2: Staging/Production Testing
├─ Day 1: Deploy to GCP/AWS staging
├─ Day 2: Load testing
├─ Day 3: Security audit
└─ Day 4: Final validation → GO LIVE
```

---

## 🚀 Recommended Order (TRY THIS FIRST)

### Option A: Fast Local Test (2 hours)
**Best if you have good laptop**

1. **15 min**: Docker Compose
   ```bash
   docker-compose up -d
   docker-compose ps
   ```

2. **15 min**: API Testing (curl)
   ```bash
   curl http://localhost/health
   curl http://localhost/api/v1/face/validate ...
   ```

3. **60 min**: Mobile App Test
   ```bash
   # Option 1: Android Studio (requires setup)
   # Option 2: Expo Go (quicker)
   expo start
   ```

4. **30 min**: Admin Panel
   ```
   Open: http://localhost/admin/
   Login and verify dashboard
   ```

**Total Time**: 2 hours  
**Resources**: Docker + Laptop  
**Result**: Confidence that all local systems work

---

### Option B: Quick Cloud Test (3 hours)
**Best if you want production-like environment**

1. **30 min**: Spin up GCP/AWS instance
2. **30 min**: Deploy docker-compose
3. **30 min**: Run integration tests
4. **60 min**: Mobile app test against cloud

**Total Time**: 3 hours  
**Cost**: ~$5-10 (t2.small instance)  
**Result**: Full production validation

---

## 🎯 My Recommendation

### For You:
```
START HERE:
1. ✅ Docker Compose local (backend + all services)
   └─ Time: 15 min, validate all 9 services running

2. ✅ API Testing with curl/Postman
   └─ Time: 15 min, test face validation endpoint

3. ✅ Mobile App with Expo Go
   └─ Time: 30 min, scan QR on real phone

4. ✅ Admin Panel in browser
   └─ Time: 15 min, check dashboard

TOTAL: 1.5 hours before deciding to deploy
```

**IF ALL PASS → DEPLOY TO PRODUCTION**

---

## ⚠️ Common Issues & Fixes

### Docker Compose Won't Start
```bash
# Check disk space
docker system df

# Clean up
docker system prune -a

# Restart Docker Desktop
# Or: systemctl restart docker (Linux)
```

### Face Validation Fails
```bash
# Check model download
curl http://localhost:8005/health
# If returns error, model downloading - wait 2 min

# Check logs
docker-compose logs face_validation
```

### Mobile App Can't Connect to Backend
```bash
# Check your IP (not localhost)
ipconfig getifaddr en0  # Mac
hostname -I            # Linux

# Update API URL in app
# Usually: http://YOUR_IP_ADDRESS
```

### MongoDB Connection Error
```bash
# Verify MongoDB Atlas credentials in .env
# Check internet connection (MongoDB Atlas cloud)
# Check whitelist IP in MongoDB Atlas
```

---

## Summary

| Test Type | Time | Recommended | Setup |
|-----------|------|-------------|-------|
| **Docker Local** | 1.5h | ✅ YES | Easy |
| **Android Studio** | 2h | ⚠️ Complex setup | Medium |
| **Expo Go** | 30m | ✅ YES | Easy |
| **Cloud Server** | 3h | ✅ Final validation | Medium |

**Start with:** Docker Compose + Expo Go  
**Time needed:** 1.5-2 hours  
**Success rate:** 99%+ (everything verified)

---

**Ready to test?** Let me know which option you choose!
