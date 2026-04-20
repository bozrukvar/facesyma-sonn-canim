# Phase 1: Compatibility & Community Foundation

**Duration:** Week 1-2  
**Status:** Ready for Development  
**Storage:** Conservative Limits (Optimize for Scale)

---

## 🎯 Phase 1 Goals

```
Week 1:
✅ Compatibility algorithm implementation
✅ Database schema creation
✅ API endpoints (compatibility check)

Week 2:
✅ Trait-based communities (auto-create)
✅ Basic community API
✅ Testing & documentation
```

---

## 📊 Storage Limits (System-Optimized)

```
NO LARGE FILES IN PHASE 1

Direct Messages:
├─ Free: 10MB total per user
├─ Premium: 100MB total per user
└─ File types: Images + PDFs only

Groups (2-5):
├─ Storage: 200MB per group
├─ File types: PDF, text docs, images
└─ Auto-cleanup: 90 days inactive

Communities:
├─ Storage: 300MB shared
├─ Moderation: Text + images only
└─ Bandwidth: Rate-limited

Future Upgrades:
→ Month 4: 2x the limits
→ Month 7: 3x the limits
→ Month 10: Scale based on capacity
```

---

## 🗄️ Database Schema (Minimal)

### **New Tables**

```sql
-- Compatibility matching
CREATE TABLE compatibility (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user1_id INT NOT NULL,
  user2_id INT NOT NULL,
  score INT (0-100),
  category VARCHAR(20), -- UYUMLU, UYUMSUZ, SAME, DIFFERENT
  golden_ratio_diff FLOAT,
  sifat_overlap INT,
  module_overlap INT,
  calculated_at TIMESTAMP,
  expires_at TIMESTAMP DEFAULT NULL,
  UNIQUE(user1_id, user2_id),
  INDEX(user1_id),
  INDEX(user2_id),
  INDEX(category)
);

-- Communities (trait-based)
CREATE TABLE communities (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  type VARCHAR(20), -- TRAIT, MODULE, CATEGORY
  trait_name VARCHAR(50) -- e.g., "Liderlik"
  description TEXT,
  member_count INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  INDEX(name),
  INDEX(type)
);

-- Community memberships
CREATE TABLE community_members (
  id INT PRIMARY KEY AUTO_INCREMENT,
  community_id INT NOT NULL,
  user_id INT NOT NULL,
  joined_at TIMESTAMP,
  harmony_level INT (0-100),
  is_mod BOOLEAN DEFAULT FALSE,
  UNIQUE(community_id, user_id),
  FOREIGN KEY(community_id) REFERENCES communities(id),
  INDEX(user_id)
);

-- Messages (separate from existing)
CREATE TABLE community_messages (
  id INT PRIMARY KEY AUTO_INCREMENT,
  from_user_id INT NOT NULL,
  to_user_id INT, -- NULL if group/community
  community_id INT,
  group_id INT,
  content TEXT,
  file_id INT,
  created_at TIMESTAMP,
  is_read BOOLEAN DEFAULT FALSE,
  INDEX(from_user_id),
  INDEX(to_user_id),
  INDEX(community_id)
);

-- File storage (minimal)
CREATE TABLE community_files (
  id INT PRIMARY KEY AUTO_INCREMENT,
  owner_id INT,
  group_id INT,
  community_id INT,
  file_name VARCHAR(255),
  file_size INT, -- bytes
  file_type VARCHAR(20), -- pdf, image, doc
  s3_path VARCHAR(500),
  uploaded_at TIMESTAMP,
  expires_at TIMESTAMP,
  download_count INT DEFAULT 0,
  INDEX(owner_id),
  INDEX(group_id)
);

-- Moderation logs (for safety)
CREATE TABLE moderation_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  community_id INT,
  action_type VARCHAR(20), -- flag, warn, block
  target_user_id INT,
  reason TEXT,
  moderator_id INT,
  status VARCHAR(20), -- pending, approved, rejected
  created_at TIMESTAMP,
  resolved_at TIMESTAMP
);
```

---

## 🛠️ Core Implementation Tasks

### **Task 1: Compatibility Algorithm**

**File:** `facesyma_backend/facesyma_revize/compatibility.py`

```python
def calculate_compatibility(user1_id, user2_id):
    """
    Returns: {score, category, can_message, reasons}
    
    Score breakdown:
    - Golden ratio match: 0-20 pts
    - Sıfat overlap: 0-40 pts
    - Module overlap: 0-20 pts
    - Conflict check: -5 pts each
    
    Categories:
    - UYUMLU: score >= 70 AND conflicts == 0
    - UYUMSUZ: score < 30 OR conflicts >= 2
    - SAME_CATEGORY: same primary trait
    - DIFFERENT_CATEGORY: complementary
    """
    pass

def find_compatible_users(user_id, limit=10):
    """Returns top 10 compatible users for matching"""
    pass

def get_conflict_pairs():
    """
    Returns conflicting trait pairs:
    - Introvert ↔ Extrovert (strong conflict)
    - Confident ↔ Insecure (medium conflict)
    - etc.
    """
    pass
```

**Inputs:**
- User profiles (golden_ratio, top_sifats, modules)
- Conflict definition matrix

**Outputs:**
- Compatibility score (0-100)
- Category (UYUMLU/UYUMSUZ/SAME/DIFFERENT)
- Messaging permission (bool)
- Reasons (array of strings)

---

### **Task 2: Community Auto-Creation**

**File:** `facesyma_backend/analysis_api/views.py`

```python
# When user completes analysis:
def post_analysis_hook(user_id, analysis_result):
    """
    Auto-add user to trait-based communities
    when they get new traits
    """
    traits = analysis_result['top_sifats']
    
    for trait in traits:
        community = get_or_create_community(trait)
        add_user_to_community(user_id, community, harmony_score=analysis_result['score'])
    
    # Trigger background job to find matches
    find_and_notify_compatible_users(user_id)
```

**Communities to create:**
```
- Liderlik (Leadership)
- Empatik (Empathy)
- Analitik (Analytical)
- Yaratıcı (Creative)
- Disiplinli (Disciplined)
- Özgüvenli (Confident)
- Sosyal (Social)
- ... (201 possible communities based on sıfats)
```

---

### **Task 3: API Endpoints (Phase 1)**

**File:** `facesyma_backend/analysis_api/urls.py` (new section)

```python
# Compatibility endpoints
path('api/v1/compatibility/check/', CheckCompatibilityView.as_view()),
path('api/v1/compatibility/find/', FindCompatibleUsersView.as_view()),
path('api/v1/compatibility/stats/', CompatibilityStatsView.as_view()),

# Community endpoints
path('api/v1/communities/', ListCommunitiesView.as_view()),
path('api/v1/communities/<id>/join/', JoinCommunityView.as_view()),
path('api/v1/communities/<id>/members/', ListCommunityMembersView.as_view()),
```

---

### **Task 4: API Implementation**

**Endpoint 1: Check Compatibility**
```bash
POST /api/v1/compatibility/check/

Request:
{
  "user1_id": 123,
  "user2_id": 456
}

Response (200):
{
  "success": true,
  "data": {
    "score": 85,
    "category": "UYUMLU",
    "can_message": true,
    "reasons": [
      "Golden ratio difference: 2.3%",
      "Shared sıfats: 5/7",
      "Same coaching modules: 3"
    ]
  }
}

Response (Incompatible):
{
  "success": true,
  "data": {
    "score": 25,
    "category": "UYUMSUZ",
    "can_message": false,
    "reasons": [
      "Conflicting traits: Introvert vs Extrovert",
      "Golden ratio difference: 12%"
    ]
  }
}
```

**Endpoint 2: Find Compatible Users**
```bash
POST /api/v1/compatibility/find/

Request:
{
  "user_id": 123,
  "limit": 10,
  "category": "UYUMLU" -- optional filter
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
      "golden_ratio": 1.615
    },
    ...
  ]
}
```

**Endpoint 3: List Communities**
```bash
GET /api/v1/communities/?type=TRAIT&limit=20

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Liderlik Topluluğu",
      "type": "TRAIT",
      "member_count": 1245,
      "description": "Lider özellikleri taşıyan kişiler..."
    },
    ...
  ]
}
```

**Endpoint 4: Join Community**
```bash
POST /api/v1/communities/1/join/

Request:
{
  "user_id": 123
}

Response:
{
  "success": true,
  "data": {
    "community_id": 1,
    "membership_status": "active",
    "access_level": "member"
  }
}
```

---

## 🧪 Testing Plan

### **Unit Tests**
```
✓ compatibility score calculation
✓ conflict detection
✓ category assignment
✓ community creation
✓ member addition
```

### **Integration Tests**
```
✓ User analysis → Auto-add to communities
✓ Compatibility check → API response
✓ Find matches → Returns correct users
✓ Join community → Update database
```

### **Load Tests**
```
✓ 1,000 users finding matches (load)
✓ Community with 10,000 members (scale)
✓ Compatibility calculation performance (<100ms)
```

---

## 📋 Deliverables

### **Week 1**
- [ ] `compatibility.py` module complete
- [ ] Database schema created & migrated
- [ ] Compatibility endpoints implemented
- [ ] Unit tests passing

### **Week 2**
- [ ] Community auto-creation logic
- [ ] Community endpoints
- [ ] Integration with analysis flow
- [ ] API documentation
- [ ] Deployment to production

---

## 🚀 Deployment Steps

```bash
# 1. Database migration
python manage.py migrate

# 2. Add data
python scripts/create_communities.py  # Create 201 trait-based communities

# 3. Deploy backend
docker-compose build backend
docker-compose up -d backend

# 4. Smoke tests
curl http://localhost:8000/api/v1/compatibility/check/ \
  -d '{"user1_id": 1, "user2_id": 2}'

# 5. Monitor
docker-compose logs -f backend
```

---

## 📈 Success Metrics (Phase 1)

```
Technical:
✓ API response time <100ms
✓ Compatibility calculation <50ms
✓ 99.9% uptime
✓ All tests passing

User Adoption:
✓ Auto-community join rate >90%
✓ Profile completion after analysis >70%
✓ Compatibility check usage >20%

Performance:
✓ Database queries optimized
✓ No N+1 queries
✓ Proper indexing on all lookups
```

---

## 🔄 Future Phases (After Week 2)

```
Phase 2: Messaging (Week 3-4)
├─ 1:1 direct messages
├─ Basic chat UI
└─ File sharing (10MB max)

Phase 3: Groups (Week 5-6)
├─ 2-5 person groups
├─ Group chat
└─ File library

Phase 4: Advanced (Week 7-8)
├─ Voice messages
├─ Video calls
└─ Collaboration tools
```

---

## ✅ Critical Decisions Made

**Storage:** Conservative limits (10MB-300MB) for system health
- Upgrade path ready for scaling
- Auto-cleanup after 90 days

**Performance:** Compatibility calculations optimized
- Cached results (expires monthly)
- Background job processing
- Rate limiting to prevent abuse

**Privacy:** All communications optional
- Users choose to join communities
- Can block/mute anytime
- Moderation ready for spam/abuse

---

**Status:** Ready for Development  
**Owner:** Backend Team  
**Next Step:** Task 1 - Compatibility Algorithm Coding
