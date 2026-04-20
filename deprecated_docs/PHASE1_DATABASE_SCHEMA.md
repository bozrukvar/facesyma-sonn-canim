# Phase 1: Database Schema & Migrations

**Status:** ✅ Implemented  
**Date:** 2026-04-14  
**Database:** MongoDB (facesyma-backend)

---

## 📋 Collections Created

### 1. **compatibility**
Kullanıcılar arası uyum skorları ve kategorileri.

```javascript
{
  _id: ObjectId,
  user1_id: Number,
  user2_id: Number,
  score: Number (0-100),
  category: String (UYUMLU | UYUMSUZ | SAME_CATEGORY | DIFFERENT_CATEGORY),
  can_message: Boolean,
  golden_ratio_diff: Float,
  sifat_overlap: Number,
  module_overlap: Number,
  conflict_count: Number,
  calculated_at: Timestamp,
  expires_at: Timestamp (TTL: 30 gün)
}
```

**Indexes:**
- `user1_id, user2_id` (UNIQUE) - Aynı çiftin iki kez kaydedilmesini önle
- `user1_id` - Hızlı user1 lookup
- `user2_id` - Hızlı user2 lookup
- `category` - Kategoriye göre filtreleme
- `calculated_at` (TTL) - 30 gün sonra otomatik silinme

---

### 2. **communities**
Sıfat/modül tabanlı topluluklar.

```javascript
{
  _id: ObjectId,
  name: String,
  type: String (TRAIT | MODULE | CATEGORY),
  trait_name: String (e.g., "Lider", "Liderlik Modülü"),
  description: String,
  founder_id: Number (0 = System),
  member_count: Number,
  is_active: Boolean (default: true),
  rules: String,
  moderation_policy: String,
  created_at: Timestamp,
  updated_at: Timestamp
}
```

**Indexes:**
- `name` - Topluluk adıyla arama
- `type` - Tipe göre filtreleme (TRAIT, MODULE, CATEGORY)
- `trait_name` - Sıfat/modül adıyla hızlı lookup
- `created_at` - Tarih sıralaması

---

### 3. **community_members**
Topluluk üyelikleri ve uyum seviyeleri.

```javascript
{
  _id: ObjectId,
  community_id: String (ObjectId),
  user_id: Number,
  joined_at: Timestamp,
  harmony_level: Number (0-100, default: 75),
  is_mod: Boolean (default: false),
  contribution_score: Number (optional)
}
```

**Indexes:**
- `community_id, user_id` (UNIQUE) - Aynı üyeliğin iki kez kaydedilmesini önle
- `user_id` - Kullanıcının tüm üyeliklerini bul
- `community_id` - Topluluğun tüm üyelerini bul
- `joined_at` - Katılış tarihine göre sıralama

---

### 4. **community_messages**
Topluluk ve grup sohbetleri.

```javascript
{
  _id: ObjectId,
  from_user_id: Number,
  to_user_id: Number (null = group/community),
  community_id: String,
  group_id: String,
  content: String,
  file_id: String (optional),
  created_at: Timestamp,
  is_read: Boolean,
  edited_at: Timestamp (optional),
  deleted_at: Timestamp (optional)
}
```

**Indexes:**
- `from_user_id` - Kullanıcıdan gelen mesajlar
- `to_user_id` - Kullanıcıya gelen mesajlar
- `community_id` - Topluluğun mesajları
- `created_at` (TTL: 90 gün) - 90 gün sonra otomatik silinme

---

### 5. **community_files**
Dosya depolaması ve meta verisi.

```javascript
{
  _id: ObjectId,
  owner_id: Number,
  community_id: String,
  group_id: String,
  file_name: String,
  file_size: Number (bytes),
  file_type: String (pdf | image | doc),
  s3_path: String,
  uploaded_at: Timestamp,
  expires_at: Timestamp,
  download_count: Number
}
```

**Indexes:**
- `owner_id` - Kullanıcının yüklediği dosyalar
- `community_id` - Topluluğun dosyaları
- `uploaded_at` - Yükleme tarihine göre sıralama
- `expires_at` (TTL) - Sona erme tarihinde otomatik silinme

---

### 6. **moderation_logs**
Moderasyon eylemleri ve raporlar.

```javascript
{
  _id: ObjectId,
  community_id: String,
  action_type: String (flag | warn | block | delete_message),
  target_user_id: Number,
  moderator_id: Number,
  reason: String,
  status: String (pending | approved | rejected),
  created_at: Timestamp,
  resolved_at: Timestamp
}
```

**Indexes:**
- `community_id` - Topluluğun moderasyon logları
- `target_user_id` - Kullanıcıya karşı alınan aksiyonlar
- `created_at` - Tarih sıralaması
- `status` - Duruma göre filtreleme (pending, approved, rejected)

---

## 🚀 Migration Script

**File:** `migrate_compatibility_db.py`

```bash
# Koleksiyonları ve indexleri oluştur
python facesyma_backend/migrate_compatibility_db.py
```

**Çıktı:**
```
📋 Compatibility & Communities DB Migration başladı...

1️⃣  Creating 'compatibility' collection...
   ✅ Indexes created: user_pair, user1_id, user2_id, category, calculated_at (TTL)

2️⃣  Creating 'communities' collection...
   ✅ Indexes created: name, type, trait_name, created_at

3️⃣  Creating 'community_members' collection...
   ✅ Indexes created: community_user (unique), user_id, community_id, joined_at

4️⃣  Creating 'community_messages' collection...
   ✅ Indexes created: from_user_id, to_user_id, community_id, created_at (TTL: 90 days)

5️⃣  Creating 'community_files' collection...
   ✅ Indexes created: owner_id, community_id, uploaded_at, expires_at (TTL)

6️⃣  Creating 'moderation_logs' collection...
   ✅ Indexes created: community_id, target_user_id, created_at, status

✅ Migration Complete!
```

---

## 📊 Storage Limits (Conservative)

| Entity | Limit | Auto-Cleanup |
|--------|-------|--------------|
| Direct Messages (Free) | 10 MB total | 30 days |
| Direct Messages (Premium) | 100 MB total | Never |
| Groups (2-5 people) | 200 MB per group | 90 days inactive |
| Communities | 300 MB shared | 90 days inactive |
| Community Messages | No limit (TTL: 90 days) | Auto-delete |
| Community Files | 300 MB (future: 2GB) | Configurable TTL |

---

## 📝 API Endpoints (Phase 1)

### Compatibility Endpoints

**POST** `/api/v1/compatibility/check/`
```bash
Request:
{
  "user1_id": 123,
  "user2_id": 456
}

Response:
{
  "success": true,
  "data": {
    "score": 85,
    "category": "UYUMLU",
    "can_message": true,
    "reasons": ["✓ Golden ratio match: 2.3% difference", ...],
    "golden_ratio_diff": 0.0234,
    "sifat_overlap": 5,
    "module_overlap": 3,
    "conflict_count": 0
  }
}
```

---

**POST** `/api/v1/compatibility/find/`
```bash
Request:
{
  "user_id": 123,
  "limit": 10,
  "category": "UYUMLU"  (optional)
}

Response:
{
  "success": true,
  "data": [
    {
      "user_id": 456,
      "username": "John",
      "score": 85,
      "category": "UYUMLU",
      "can_message": true,
      "golden_ratio": 1.615,
      "top_sifats": ["Lider", "Disiplinli"]
    },
    ...
  ],
  "count": 10
}
```

---

**GET** `/api/v1/compatibility/stats/?user_id=123`
```bash
Response:
{
  "success": true,
  "data": {
    "total_uyumlu": 42,
    "total_uyumsuz": 15,
    "total_same_category": 28,
    "total_different_category": 8,
    "avg_score": 67.5,
    "highest_score": 95,
    "lowest_score": 15
  }
}
```

---

### Community Endpoints

**GET** `/api/v1/communities/?type=TRAIT&limit=20`
```bash
Response:
{
  "success": true,
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Liderlik Topluluğu",
      "type": "TRAIT",
      "trait_name": "Lider",
      "member_count": 1245,
      "description": "Lider özellikleri taşıyan kişiler...",
      "created_at": 1712000000
    },
    ...
  ],
  "count": 20
}
```

---

**POST** `/api/v1/communities/{id}/join/`
```bash
Request:
{
  "user_id": 123
}

Response:
{
  "success": true,
  "data": {
    "community_id": "507f1f77bcf86cd799439011",
    "user_id": 123,
    "membership_status": "active",
    "harmony_level": 75,
    "joined_at": 1712000000
  }
}
```

---

**GET** `/api/v1/communities/{id}/members/?sort_by=harmony&limit=50`
```bash
Response:
{
  "success": true,
  "data": [
    {
      "user_id": 123,
      "username": "John",
      "harmony_level": 85,
      "joined_at": 1712000000,
      "is_mod": false
    },
    ...
  ],
  "count": 50
}
```

---

## 🔗 MongoDB Collection Functions

**File:** `admin_api/utils/mongo.py`

```python
# Yeni getter functions
get_compatibility_col()          # compatibility
get_communities_col()             # communities
get_community_members_col()       # community_members
get_community_messages_col()      # community_messages
get_community_files_col()         # community_files
get_moderation_logs_col()         # moderation_logs
```

---

## 🎯 Community Auto-Creation Hook

**File:** `analysis_api/community_hooks.py`

Kullanıcı karakter analizi yaptığında otomatik olarak sıfat/modül topluluklarına eklenir.

```python
# Tetikleme (views.py içinde)
from community_hooks import auto_add_to_communities

result = calculate_compatibility(...)
if uid:
    auto_add_to_communities(uid, result)
    # → Otomatik olarak trait ve module topluluklarına ekleme
```

---

## 📋 Checklist

**Week 1:**
- [x] Compatibility algorithm (`compatibility.py`)
- [x] Database collections & indexes
- [x] Migration script
- [x] API endpoints (6 endpoints)
- [ ] Unit tests (TBD)
- [ ] Integration tests (TBD)

**Week 2:**
- [ ] Community auto-creation testing
- [ ] API integration testing
- [ ] Load testing
- [ ] Deployment

---

## 🔄 Future Enhancements

**Month 2:**
- Direct messaging (1:1 UYUMLU only)
- File sharing (max 50MB per user)
- Message notifications

**Month 3:**
- Small groups (2-5 people)
- Group chat
- File library

**Month 4+:**
- Voice messaging
- Video calls
- Community forums

---

**Status:** Ready for Testing  
**Next Step:** Unit & Integration Tests (TASK 5)
