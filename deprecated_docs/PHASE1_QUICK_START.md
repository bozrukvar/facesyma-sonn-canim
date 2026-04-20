# Phase 1: Quick Start Guide

**Compatibility & Community System** — Ready for Testing & Deployment

---

## 🚀 Quick Deployment (5 minutes)

### 1. Initialize Database

```bash
cd facesyma_backend
python migrate_compatibility_db.py
```

**Expected Output:**
```
📋 Compatibility & Communities DB Migration başladı...

1️⃣  Creating 'compatibility' collection...
   ✅ Indexes created: user_pair, user1_id, user2_id, category, calculated_at (TTL)

2️⃣  Creating 'communities' collection...
   ✅ Indexes created: name, type, trait_name, created_at

...

✅ Migration Complete!
```

### 2. Restart Backend

```bash
docker-compose down backend
docker-compose up -d backend
```

### 3. Verify Health

```bash
curl -X GET http://localhost:8000/api/v1/communities/?limit=1
```

**Expected Response:**
```json
{
  "success": true,
  "data": [],
  "count": 0
}
```

---

## 📡 API Endpoints (6 Total)

### Compatibility Checking

#### Check Two Users
```bash
curl -X POST http://localhost:8000/api/v1/compatibility/check/ \
  -H "Content-Type: application/json" \
  -d '{
    "user1_id": 1,
    "user2_id": 2
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "score": 78,
    "category": "UYUMLU",
    "can_message": true,
    "reasons": [
      "✓ Golden ratio match: 3.2% difference (Very good)",
      "✓ Shared sıfats: 4/6 (67%)",
      "✓ Shared modules: 2/3"
    ],
    "golden_ratio_diff": 0.032,
    "sifat_overlap": 4,
    "module_overlap": 2,
    "conflict_count": 0
  }
}
```

#### Find Compatible Users
```bash
curl -X POST http://localhost:8000/api/v1/compatibility/find/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "limit": 5,
    "category": "UYUMLU"
  }'
```

#### User Compatibility Stats
```bash
curl -X GET "http://localhost:8000/api/v1/compatibility/stats/?user_id=1"
```

### Community Management

#### List Communities
```bash
curl -X GET "http://localhost:8000/api/v1/communities/?type=TRAIT&limit=20"
```

#### Join Community
```bash
curl -X POST http://localhost:8000/api/v1/communities/507f1f77bcf86cd799439011/join/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1
  }'
```

#### List Community Members
```bash
curl -X GET "http://localhost:8000/api/v1/communities/507f1f77bcf86cd799439011/members/?sort_by=harmony&limit=50"
```

---

## 🧪 Testing Checklist

### Unit Tests (Pending)
- [ ] Test compatibility calculation
- [ ] Test conflict detection
- [ ] Test category assignment
- [ ] Test auto-community creation

### Integration Tests (Pending)
- [ ] Test full analysis → auto-add flow
- [ ] Test API endpoints
- [ ] Test database constraints
- [ ] Test error handling

### Manual Testing

#### 1. Create Two Users (if not exist)
```bash
# Assuming admin API allows user creation or use existing users
# For testing, assume user_id 1 and 2 exist with profiles
```

#### 2. Check Compatibility
```bash
curl -X POST http://localhost:8000/api/v1/compatibility/check/ \
  -H "Content-Type: application/json" \
  -d '{"user1_id": 1, "user2_id": 2}'
```

**Verify:**
- ✓ Response status 200
- ✓ Success field is true
- ✓ Score between 0-100
- ✓ Category is valid (UYUMLU/UYUMSUZ/SAME_CATEGORY/DIFFERENT_CATEGORY)
- ✓ can_message is boolean

#### 3. Find Compatible Users
```bash
curl -X POST http://localhost:8000/api/v1/compatibility/find/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "limit": 5}'
```

**Verify:**
- ✓ Returns array of users
- ✓ Each user has score and category
- ✓ Results sorted by score (descending)

#### 4. List Communities
```bash
curl -X GET "http://localhost:8000/api/v1/communities/?limit=5"
```

**Verify:**
- ✓ Returns array of communities
- ✓ Each has: name, type, member_count
- ✓ Type is TRAIT or MODULE

#### 5. Join Community
```bash
COMMUNITY_ID="<from list response>"
curl -X POST http://localhost:8000/api/v1/communities/$COMMUNITY_ID/join/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**Verify:**
- ✓ Status 200
- ✓ Returns membership_status: "active"
- ✓ harmony_level is set (default: 75)

#### 6. List Members
```bash
curl -X GET "http://localhost:8000/api/v1/communities/$COMMUNITY_ID/members/?limit=10"
```

**Verify:**
- ✓ Returns array of members
- ✓ Includes user_id, username, harmony_level
- ✓ Sorted by harmony_level (descending)

---

## 📊 Test Data

For testing, you'll need 2+ users with profiles:

```javascript
{
  "id": 1,
  "username": "Ali",
  "golden_ratio": 1.618,
  "top_sifats": ["Lider", "Disiplinli", "Analitik"],
  "modules": ["Liderlik", "Kariyer", "İletişim"]
}

{
  "id": 2,
  "username": "Ayşe",
  "golden_ratio": 1.625,
  "top_sifats": ["Lider", "Sosyal", "Analitik"],
  "modules": ["Liderlik", "Duygusal Zeka", "İletişim"]
}
```

**Expected Result:**
- Compatibility score: ~78 (high match)
- Category: UYUMLU (compatible)
- Can message: true

---

## 🔍 Monitoring & Debugging

### Check MongoDB Collections
```bash
# Connect to MongoDB
mongo "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/facesyma-backend"

# List collections
show collections

# Check compatibility records
db.compatibility.find().limit(5)

# Check communities
db.communities.find().limit(5)

# Check community members
db.community_members.find().limit(5)
```

### Check Django Logs
```bash
docker-compose logs -f backend | grep compatibility
docker-compose logs -f backend | grep community
```

### Check Indexes
```bash
mongo <connection>
db.compatibility.getIndexes()
db.communities.getIndexes()
db.community_members.getIndexes()
```

---

## ⚙️ Configuration

### Environment Variables

**Required (.env):**
```bash
MONGO_URI=mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/facesyma-backend?...
JWT_SECRET=facesyma-jwt-secret-change-in-production
DJANGO_SECRET_KEY=django-secret-key
```

**Optional:**
```bash
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,example.com
```

---

## 📈 Performance Expectations

| Operation | Expected Time | Status |
|-----------|----------------|--------|
| Compatibility check | <50ms | Algorithm optimized |
| Find 10 compatible | <100ms | Indexed queries |
| List 20 communities | <30ms | Cached results |
| Join community | <20ms | Direct insert |
| List 50 members | <100ms | Aggregation |

---

## 🐛 Troubleshooting

### Issue: "Compatibility modülü yüklenemedı"
**Solution:** Check that `facesyma_revize` is in FACESYMA_ENGINE_PATH

### Issue: "Topluluk bulunamadı" (404)
**Solution:** Communities are created automatically on first user analysis. Run migration script first.

### Issue: "MongoDB connection timeout"
**Solution:** Check MONGO_URI in .env. Verify network access to MongoDB cluster.

### Issue: "Kullanıcılardan biri bulunamadı" (404)
**Solution:** User profiles must exist in appfaceapi_myuser collection. Ensure users are created before testing.

### Issue: Response time slow (>500ms)
**Solution:**
1. Check MongoDB indexes: `python manage.py shell`
2. Check database size: `db.stats()`
3. Add EXPLAIN to queries to verify index usage

---

## 📚 Documentation Files

1. **PHASE1_IMPLEMENTATION_PLAN.md** — Original plan & architecture
2. **PHASE1_DATABASE_SCHEMA.md** — Complete database documentation
3. **PHASE1_IMPLEMENTATION_STATUS.md** — Detailed status & metrics
4. **This file** — Quick start & testing guide

---

## ✅ Pre-Production Checklist

- [ ] Database migration script runs successfully
- [ ] All 6 API endpoints respond correctly
- [ ] Compatibility algorithm produces expected scores
- [ ] Communities are auto-created on analysis
- [ ] Error handling works (invalid inputs)
- [ ] Logging is configured and working
- [ ] Performance meets expectations (<100ms)
- [ ] No N+1 queries detected
- [ ] CORS headers are correct
- [ ] JWT authentication works (if required)
- [ ] Database backups are configured
- [ ] Monitoring & alerts are set up

---

## 🚀 Deployment Commands

```bash
# 1. Backup current database
mongodump --uri="$MONGO_URI" --out=backup_$(date +%s)

# 2. Run migration
python migrate_compatibility_db.py

# 3. Verify
curl -X GET http://localhost:8000/api/v1/communities/?limit=1

# 4. Monitor
docker-compose logs -f backend

# 5. Smoke test (after 5 mins)
curl -X POST http://localhost:8000/api/v1/compatibility/check/ \
  -H "Content-Type: application/json" \
  -d '{"user1_id": 1, "user2_id": 2}'
```

---

**Status:** Ready for TASK 5 (Unit Tests)  
**Last Updated:** 2026-04-14  
**Next Phase:** Phase 2 (Messaging & Groups)
