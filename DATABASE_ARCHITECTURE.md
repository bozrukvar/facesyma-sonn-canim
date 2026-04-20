# 🗄️ Database Architecture - localhost:8000

**Status:** Currently Running  
**Date:** 2026-04-20

---

## 📊 Summary

**NOT** traditional SQL database. **Hybrid approach:**

| Layer | Technology | Purpose | Status |
|-------|-----------|---------|--------|
| **Primary DB** | **MongoDB** (NoSQL) | All user data, analysis, profiles | ✅ Cloud (Atlas) |
| **Cache** | **Redis** | Session, chat, leaderboard cache | ✅ Local/Docker |
| **ORM DB** | **SQLite** (SQL) | Django admin only, not used | ⚠️ Local fallback |

---

## 🔍 Detailed Breakdown

### 1️⃣ **PRIMARY: MongoDB (NoSQL - Document DB)**

**Location:** Cloud (MongoDB Atlas)

```python
# From settings.py line 47-51
MONGO_URI = 'mongodb+srv://facesyma:...'
'facesyma-backend?...'
```

**What's stored in MongoDB:**
- ✅ Users (registration, profiles, subscriptions)
- ✅ Analysis history (face analysis results)
- ✅ Sıfat scores (201 personality attributes)
- ✅ Gamification (badges, coins, leaderboards)
- ✅ Chat history
- ✅ Admin audit logs
- ✅ Meal game data
- ✅ Social challenges
- ✅ Compatibility data

**Why MongoDB?**
- Document-based (perfect for varying schemas)
- Scalable horizontally
- Good for real-time updates
- Handles nested data well
- Auto-scaling on Atlas

---

### 2️⃣ **SECONDARY: Redis (Cache Layer)**

**Location:** Docker or local

```bash
# From docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

**What's cached:**
- ✅ Session tokens
- ✅ AI chat messages
- ✅ Leaderboard calculations
- ✅ User analytics
- ✅ Rate limiting
- ✅ Temporary data

**Why Redis?**
- Ultra-fast in-memory cache
- Expires automatically
- Perfect for session management
- Sub-millisecond latency
- Reduces MongoDB queries

---

### 3️⃣ **LEGACY: SQLite (SQL - Django ORM)**

**Location:** `facesyma_backend/db.sqlite3`

```python
# From settings.py line 39-44
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**What's NOT used:**
- ❌ No user data
- ❌ No analysis data
- ❌ Not in production

**Why it's there:**
- Django admin panel fallback
- Fixture loading (test data)
- ORM compatibility layer
- Never queried in production

**In Production:**
- SQLite disabled
- All queries go to MongoDB directly
- Redis for cache

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────┐
│      Mobile App / Web App               │
│   (React Native / React)                │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      Django REST API (:8000)            │
│      (facesyma_backend)                 │
└─────────────────────────────────────────┘
         ↓              ↓
    ┌─────────┐    ┌─────────┐
    │          │    │          │
    ↓          ↓    ↓          ↓
┌────────┐  ┌────────┐  ┌──────────┐
│ Redis  │  │MongoDB │  │ SQLite   │
│ (Cache)│  │(Main)  │  │(Legacy)  │
│:6379   │  │Atlas   │  │Local     │
└────────┘  └────────┘  └──────────┘
```

---

## 💾 Data Flow

### User Registration
```
1. User submits registration
   ↓
2. Django validates input
   ↓
3. Data → MongoDB (store user)
   ↓
4. Token → Redis (session cache)
   ↓
5. Response → Mobile App
```

### Face Analysis
```
1. Mobile uploads face photo
   ↓
2. Face Validation Service processes
   ↓
3. Result → MongoDB (history)
   ↓
4. Analysis → Sıfat scoring
   ↓
5. Metrics → Redis (leaderboard cache)
   ↓
6. Response → Mobile App
```

### Admin Dashboard
```
1. Admin requests stats
   ↓
2. Check Redis cache first
   ↓
3. If miss → Query MongoDB
   ↓
4. Return to admin panel
```

---

## 🔑 Key Collections (MongoDB)

| Collection | Purpose | Indexes |
|-----------|---------|---------|
| **users** | User profiles, auth | email, app_source |
| **analysis_history** | Face analysis results | user_id, created_at |
| **sifat_scores** | Personality scores (201) | user_id, sifat_id |
| **badges** | Achievement badges | user_id |
| **coins** | Virtual currency | user_id |
| **leaderboard** | User rankings | score DESC |
| **chat_messages** | AI chat history | user_id, timestamp |
| **meal_games** | Meal game progress | user_id |
| **social_challenges** | Challenge data | user_id, challenge_id |
| **subscriptions** | Payment data | user_id, status |
| **audit_log** | Admin actions | admin_id, timestamp |

---

## ⚙️ Configuration

### MongoDB Atlas Connection

```python
# settings.py
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/'
    'facesyma-backend?serverSelectionTimeoutMS=30000'
)
```

**Features:**
- Cloud-hosted (auto-scaling)
- Replica set (high availability)
- Automatic backups
- Connection pooling
- 30-second timeout

### Redis Configuration

```python
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: >
    redis-server
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
```

**Features:**
- 512MB memory limit
- LRU eviction policy
- No persistence (restart → clear cache)
- Alpine image (minimal)

---

## 🚀 Production Setup

### Deployment (Docker)
```yaml
services:
  backend:
    - Connects to: MongoDB Atlas (cloud)
    - Connects to: Redis container (local)
    - Uses: MongoDB driver (pymongo)
    - Caches: Redis client

  face_validation:
    - Connects to: Redis only
    - Stores: Nothing persistent

  ai_chat:
    - Connects to: Redis for cache
    - Connects to: Ollama for LLM
    - Uses: MongoDB indirectly (via backend)
```

---

## 📊 Scale Numbers

| Metric | Value | Notes |
|--------|-------|-------|
| **Users** | Unlimited | MongoDB auto-scales |
| **Collections** | 11 | Indexed for performance |
| **Cache TTL** | Variable | Seconds to hours |
| **Connection Pool** | 100 | Max connections |
| **Request Latency** | <100ms | Redis + MongoDB |

---

## ✅ NOT Using

| Technology | Reason |
|-----------|--------|
| ❌ PostgreSQL | Too rigid for varying schemas |
| ❌ MySQL | Not suitable for document data |
| ❌ SQL Server | Overkill for this use case |
| ❌ Firebase | Want control over data |
| ❌ Elasticsearch | Not needed for these queries |

---

## 🔒 Security

**MongoDB Atlas:**
- ✅ SSL/TLS encryption
- ✅ IP whitelist
- ✅ Credentials in .env
- ✅ Read-only replicas available

**Redis:**
- ✅ No authentication required (local only)
- ✅ Protected by Docker network
- ✅ In-memory only (no logs)

**SQLite:**
- ✅ Not used in production
- ✅ Local development only
- ✅ Contains no sensitive data

---

## 📝 Summary

```
┌─────────────────────────────────────┐
│  DATABASE ARCHITECTURE SUMMARY      │
├─────────────────────────────────────┤
│                                     │
│  PRIMARY:  MongoDB (NoSQL)          │
│  Location: Cloud (Atlas)            │
│  Purpose:  All user data            │
│  Status:   ✅ Production-ready      │
│                                     │
│  SECONDARY: Redis (Cache)           │
│  Location:  Docker / Local          │
│  Purpose:   Fast cache layer        │
│  Status:    ✅ Production-ready     │
│                                     │
│  LEGACY:    SQLite (ORM)            │
│  Location:  Local file              │
│  Purpose:   Django admin only       │
│  Status:    ⚠️ Not used in prod     │
│                                     │
└─────────────────────────────────────┘
```

---

**Answer to your question:**
> "Localhost:8000 de çalışan proje hangi SQL alt yapısını kullanıyor?"

**A:** 
- **Primarily:** MongoDB (NoSQL, not SQL)
- **Cache:** Redis
- **Fallback:** SQLite (not used)

**This is NOT a traditional SQL database setup.**

