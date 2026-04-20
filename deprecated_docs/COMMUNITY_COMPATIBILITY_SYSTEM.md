# Facesyma Community & Compatibility Matching System

**Status:** Planning & Architecture  
**Date:** 2026-04-14  
**Priority:** HIGH (Revenue + Engagement)

---

## 📋 System Overview

Kullanıcıların **uyum durumlarına** göre gruplandırılıp, topluluklar oluşturması, iletişim kurması, dosya paylaşması ve ortak coachinge katılması sistemi.

### **3 Ana Segment**

```
┌─────────────────────────────────────────────┐
│  COMPATIBILITY MATCHING & COMMUNITIES       │
├─────────────────────────────────────────────┤
│ 1. ONE-TO-ONE                               │
│    ├─ Uyumlu: Direct messaging              │
│    ├─ Uyumsuz: Blocked/Limited              │
│    └─ Same Category: Shared insights        │
│                                             │
│ 2. SMALL GROUPS (2-5 people)               │
│    ├─ Twin analysis (var)                   │
│    ├─ Group chat                            │
│    ├─ Shared files                          │
│    └─ Combined coaching paths               │
│                                             │
│ 3. LARGE COMMUNITIES (5+ people)           │
│    ├─ Category-based groups                 │
│    ├─ Module-based groups                   │
│    ├─ Trait-based circles                   │
│    ├─ Group coaching modules                │
│    └─ File library + knowledge base         │
└─────────────────────────────────────────────┘
```

---

## 🎯 Compatibility Categories

### **UYUMLU (Compatible)**
**Koşul:** Shared traits/modules ≥ 70%
```
Örnek: 
- İkisi de "Lider" + "Disiplinli"
- Aynı coaching modules'e abone
- Golden ratio scores benzer (±5%)
- Sıfat kategorileri örtüşüyor
```

**Özel Alanlar:**
- 1:1 Private Chat (Direct message)
- Shared coaching progress
- Mutual file storage
- Collaboration recommendations

---

### **UYUMSUZ (Incompatible)**
**Koşul:** Conflicting traits OR < 30% overlap
```
Örnek:
- Biri "İçedönük" diğeri "Dışadönük"
- Karşıt sıfatlar (Özgüven vs İçine kapalı)
- Coaching hedefleri çatışıyor
```

**Kısıtlamalar:**
- No direct messaging (protection)
- Can view public profiles (read-only)
- Can join separate communities
- Optional: Suggest compatibility coaching

---

### **SAME CATEGORY (Aynı Kategori)**
**Koşul:** Same primary trait category
```
Örnek:
- İkisi de "Liderlik" kategorisinde
- Aynı coaching module'de
- Benzer sıfat profili
```

**Özel Alanlar:**
- Category-specific forums
- Shared learning circles
- Peer coaching partnerships
- Industry-specific networking

---

### **DIFFERENT CATEGORY (Farklı Kategori)**
**Koşul:** Complementary traits (non-conflicting)
```
Örnek:
- "Lider" + "Empatik"
- "Analitik" + "Kreatif"
- İç uyum: ≥ 50%
```

**Özel Alanlar:**
- Cross-functional teams
- Diverse perspectives forums
- Mentorship opportunities
- Complementary skills networks

---

## 📱 Community Types

### **TYPE 1: Trait-Based Communities**

**Yapı:**
```
Leadership Community
├─ Members: Tüm "Lider" sıfatlı kullanıcılar
├─ Size: 100-10,000+ members
├─ Features:
│  ├─ Master forum (tartışmalar)
│  ├─ Sub-groups (uyum düzeyine göre)
│  ├─ Shared coaching modules
│  ├─ Resource library
│  └─ Monthly challenges
├─ Moderation: Automated + volunteer mods
└─ Growth: Auto-add when user gets trait
```

**Sub-structure:**
```
Leadership Community
├─ UYUMLU Circle (High harmony)
│  ├─ Private chat rooms
│  ├─ Advanced coaching
│  └─ Leadership retreats
│
├─ SAME CATEGORY Group (Peers)
│  ├─ Forum + discussions
│  ├─ Shared resources
│  └─ Monthly meetups
│
└─ LEARNING PATH (Non-conflicting)
   ├─ Public forums
   ├─ Mentorship matching
   └─ Skill exchange
```

---

### **TYPE 2: Module-Based Communities**

**Yapı:**
```
Career Advancement Module
├─ Members: Module'e abone olanlar
├─ Coaching: Shared learning path
├─ Features:
│  ├─ Progress tracking (collective)
│  ├─ Peer feedback
│  ├─ Template library
│  ├─ Success stories
│  └─ Weekly group calls
├─ Certification: Group progress badge
└─ Pricing: Group rate discounts
```

---

### **TYPE 3: Micro-Groups (2-5 people)**

**Yapı:**
```
Twin Analysis Groups
├─ Size: 2-5 people (must be UYUMLU)
├─ Created: Auto or manual
├─ Duration: 4-12 weeks
├─ Features:
│  ├─ Shared analysis dashboard
│  ├─ Group coaching sessions
│  ├─ File sharing (max 100MB)
│  ├─ Weekly check-ins
│  ├─ Progress visualization
│  └─ Completion certificate
├─ Pricing: Group discounts (3-5 people)
└─ Next: Upgrade to large community
```

---

## 🗣️ Communication Features

### **MESSAGING SYSTEM**

```
Tier 1: One-to-One (UYUMLU only)
├─ Direct messages
├─ File sharing (up to 50MB)
├─ Voice notes (encrypted)
├─ Scheduled messages
├─ Message history (30 days free, archive premium)
└─ Block/Report system

Tier 2: Small Group Chat (2-5)
├─ Group messages
├─ Pinned messages
├─ File library (up to 500MB)
├─ Voice calls (p2p or group)
├─ Meeting scheduling
└─ Transcripts (premium)

Tier 3: Community Forums
├─ Threaded discussions
├─ Moderated + flagged content
├─ Search + tags
├─ Pinned announcements
├─ Member directory
└─ Voting system (upvote/helpful)
```

---

## 📁 File Sharing System

### **Storage Tiers** (System-Optimized)

```
Free User:
├─ Direct message files: 10MB total
├─ Group files: Excluded
└─ Expiry: 30 days (auto-delete)

Premium User:
├─ Direct message files: 100MB total
├─ Group files: 200MB per group
├─ Community access: 50MB shared
└─ Expiry: Unlimited

Group Owner:
├─ Group storage: 500MB (scalable to 2GB)
├─ Document library: PDF/text only initially
├─ File permissions: Custom
└─ Analytics: Access logs

Community:
├─ Community storage: 300MB shared
├─ File types: PDF, images, text docs
├─ Auto-cleanup: 90 days inactive = delete
└─ Bandwidth: Rate-limited per user
```

**Future Upgrade Path:**
```
Month 1-3: Current (small limits)
Month 4-6: Premium → 500MB, Group → 1GB
Month 7-9: Premium → 1GB, Group → 2GB
Month 10+: Scale based on infrastructure
```

### **Shared File Types**

```
📄 Documents
├─ Coaching worksheets
├─ Progress templates
├─ Goal planners
└─ PDF guides

📊 Data
├─ Analysis results
├─ Progress charts
├─ Shared dashboards
└─ CSV exports

📝 Notes
├─ Collaborative notes
├─ Meeting minutes
├─ Group journal
└─ Wiki pages

📸 Media
├─ Photos
├─ Screenshots
├─ Videos (max 500MB)
└─ Voice messages
```

---

## 🎯 Matching Algorithm

### **Compatibility Score Calculation**

```python
def calculate_compatibility(user1, user2):
    """
    Returns: 0-100 score + category
    """
    
    score = 0
    
    # Golden Ratio Match (20 points)
    ratio_diff = abs(user1.golden_ratio - user2.golden_ratio)
    if ratio_diff <= 0.05:
        score += 20
    elif ratio_diff <= 0.10:
        score += 15
    elif ratio_diff <= 0.15:
        score += 10
    
    # Sıfat Overlap (40 points)
    shared_sifats = len(set(user1.top_sifats) & set(user2.top_sifats))
    sifat_score = (shared_sifats / len(user1.top_sifats)) * 40
    score += sifat_score
    
    # Module Overlap (20 points)
    shared_modules = len(set(user1.modules) & set(user2.modules))
    module_score = (shared_modules / max(len(user1.modules), 1)) * 20
    score += module_score
    
    # Conflict Check (Subtract if incompatible)
    conflicting_sifats = CONFLICT_PAIRS
    conflicts = len(set(user1.sifats) & set(conflicting_sifats[user2.sifats]))
    score -= (conflicts * 5)
    
    # Categorize
    if score >= 70 and conflicts == 0:
        category = "UYUMLU"
    elif score < 30 or conflicts >= 2:
        category = "UYUMSUZ"
    elif same_category(user1, user2):
        category = "SAME_CATEGORY"
    else:
        category = "DIFFERENT_CATEGORY"
    
    return {
        'score': max(0, min(100, score)),
        'category': category,
        'reasons': [...]
    }
```

---

## 🚀 Feature Rollout Phases

### **PHASE 1: Foundation (Week 1-2)**
```
✅ Compatibility matching algorithm
✅ Trait-based communities (auto-created)
✅ Basic messaging (1:1 UYUMLU only)
✅ Database schema updates
✅ API endpoints
```

### **PHASE 2: Groups (Week 3-4)**
```
✅ 2-5 person group creation
✅ Twin/group analysis endpoint
✅ Group chat system
✅ File sharing (basic)
✅ Group dashboard
```

### **PHASE 3: Large Communities (Week 5-6)**
```
✅ Module-based communities
✅ Community forums
✅ Moderation tools
✅ Community analytics
✅ Member directory
```

### **PHASE 4: Advanced Features (Week 7-8)**
```
✅ Voice messaging
✅ Video calls (1:1 + group)
✅ Collaborative documents
✅ Knowledge base/wiki
✅ Community monetization
```

---

## 📊 API Endpoints (New)

### **Compatibility**
```
POST   /api/v1/compatibility/check/
       → compare_users(user1_id, user2_id)
       ← {score, category, can_message, reasons}

POST   /api/v1/compatibility/find/
       → find_matches(user_id, category?, limit=10)
       ← [{user, score, category}...]

GET    /api/v1/compatibility/stats/
       → user_compatibility_stats(user_id)
       ← {total_uyumlu, total_uyumsuz, avg_score}
```

### **Communities**
```
GET    /api/v1/communities/
       → list_communities(category?, type?)
       ← [{community_info}...]

POST   /api/v1/communities/{id}/join/
       → join_community(community_id)
       ← {membership_status, access_level}

GET    /api/v1/communities/{id}/members/
       → list_members(community_id, sort_by_harmony)
       ← [{member, uyum_score}...]
```

### **Messaging**
```
POST   /api/v1/messages/send/
       → send_message(to_user_id, content, files?)
       ← {message_id, timestamp}

GET    /api/v1/messages/conversations/
       → list_conversations(user_id)
       ← [{conversation, last_message, unread_count}...]

POST   /api/v1/groups/create/
       → create_group(name, members[], modules?)
       ← {group_id, invite_link}
```

### **Files**
```
POST   /api/v1/files/upload/
       → upload_file(file, to_group/to_user)
       ← {file_id, storage_used}

GET    /api/v1/files/shared/
       → list_shared_files(group_id)
       ← [{file_info, metadata}...]

DELETE /api/v1/files/{id}/
       → delete_file(file_id)
```

---

## 💾 Database Schema

### **New Tables**

```sql
-- Communities
communities (
  id, name, type, category, description,
  founder_id, created_at, member_count,
  rules, moderation_policy, is_active
)

-- Community Memberships
community_members (
  community_id, user_id, joined_at,
  role (member/mod/owner), harmony_level,
  contribution_score
)

-- Compatibility Matrix
compatibility (
  user1_id, user2_id, score, category,
  golden_ratio_diff, sifat_overlap,
  module_overlap, last_updated
)

-- Messages (new table or extend)
messages (
  id, from_user_id, to_user_id/group_id,
  content, file_ids[], timestamp,
  is_read, edited_at, deleted_at
)

-- Groups (micro-communities)
groups (
  id, name, creator_id, members[],
  module_id, status (active/completed),
  created_at, end_date
)

-- Files
files (
  id, owner_id, group_id, file_path,
  file_type, size, uploaded_at,
  accessed_by[], expiry_date
)

-- Community Rules/Moderation
moderation_logs (
  id, community_id, action_type,
  target_user_id, reason, moderator_id,
  timestamp, status (pending/approved/rejected)
)
```

---

## 🔒 Privacy & Safety

### **Protection Levels**

```
UYUMLU Users:
✅ Full messaging
✅ Shared files
✅ Video calls
✓ Profile visibility: Full

UYUMSUZ Users:
❌ No direct messaging
❌ No shared files
✅ Can view public profile only
✓ Can block each other

SAME/DIFFERENT Category:
⚠️  Limited messaging
⚠️  File preview only
✅ Forum participation
```

### **Moderation**

```
Automated:
- Spam detection
- Toxic language filter
- Account age check (new users)
- Rate limiting

Manual:
- Community moderators
- Report review
- Ban/suspension decisions
- Appeal process
```

---

## 💰 Monetization

### **Premium Features** (Optimized)

```
Community Owner:
- Storage: 500MB (upgrade path: 2GB later)
- Analytics: Basic community stats
- Moderation: Tools + reports
- Pricing: 199₺/month

Group Leader (2-5 people):
- Storage: 200MB per group
- Priority support
- Meeting scheduling
- Pricing: 79₺/month

Community Member:
- Messaging: Unlimited
- File storage: 100MB direct messages
- Community access: All public forums
- Pricing: 19₺/month

NOTE: Pricing starts LOW, can increase as infrastructure scales
```

---

## 📈 Success Metrics

```
Engagement:
- Daily active users in communities
- Messages per user/day
- File sharing frequency
- Group formation rate

Growth:
- Community member growth
- Cross-community migrations
- New group creations
- Retention after 30/60/90 days

Revenue:
- Premium conversion rate (40-50%)
- ARPU (Average Revenue Per User)
- LTV (Lifetime Value)
- Churn rate (<5%)
```

---

## 🎬 Implementation Timeline

```
Week 1-2: Foundation (Compatibility + Basic Communities)
Week 3-4: Groups & Messaging
Week 5-6: Forums & Advanced Features
Week 7-8: Monetization & Analytics
Week 9: Mobile App Integration
Week 10: Launch & Monitor
```

---

## ✅ Checklist

- [ ] Compatibility algorithm designed
- [ ] Database schema finalized
- [ ] API endpoints specified
- [ ] Community moderation rules
- [ ] Privacy policy updated
- [ ] User research (interviews)
- [ ] Wireframes/mockups
- [ ] Backend implementation
- [ ] Frontend components
- [ ] Mobile app integration
- [ ] Testing (QA)
- [ ] Beta launch
- [ ] Full launch

---

**Status:** Ready for Architecture Review & Development Planning  
**Owner:** Product Team  
**Next Step:** Backend Development (Phase 1)
