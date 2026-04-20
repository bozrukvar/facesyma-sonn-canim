# Consent & Approval System

**Status:** ✅ Implemented  
**Date:** 2026-04-14  
**Priority:** HIGH (KVKK/GDPR Compliance)

---

## 📋 Overview

Bu dokuman, Facesyma'da **hiçbir sohbetin veya topluluk katılımının kullanıcının onayı olmadan başlamayacağını** garantileyen onay sistemi (Consent & Approval System) hakkındadır.

### 🔐 Temel Kural

```
❌ KAPALIN: Otomatik üyelik, otomatik sohbet başlatma
✅ DOĞRU: Davet → Bekleyiş → Kullanıcı Onayı → Aktif Üyelik
```

---

## 🔄 Workflow

### Flow 1: Community Invitation (Topluluk Daveti)

```
1️⃣  Kullanıcı Analiz Yapıyor
    └─> Yüz Analizi Tamamlanıyor

2️⃣  Auto-Add Hook Tetikleniyor
    └─> Uyumlu Topluluklar Belirleniyor
    └─> ⚠️ STATUS: "pending" (ONAY BEKLEMEDE)
    └─> Davet Gönderiliyor (Bildirim)

3️⃣  Kullanıcı Davetleri Görüyor
    └─ GET /api/v1/communities/invitations/pending/?user_id=123
    └─ Bekleyen davetyielerin listesi

4️⃣  Kullanıcı Kararını Veriyor
    ├─ ✅ ONAYLA
    │  └─ POST /api/v1/communities/{id}/approve/
    │  └─ STATUS: "active"
    │  └─ Topluluk üyesi oldu, sohbet başlayabiliyor
    │
    └─ ❌ REDDET
       └─ POST /api/v1/communities/{id}/approve/
       └─ {"action": "reject"}
       └─ STATUS: "rejected"
       └─ Davetiye reddedildi, sonra tekrar davet gönderilebilir
```

---

## 📊 Member Status Values

Community members collection'ında `status` field'ı:

| Status | Anlam | Sohbet? | Notlar |
|--------|-------|---------|--------|
| `pending` | Onay bekleme | ❌ Hayır | Kullanıcı davetyiyi henüz görmedi/karar vermedi |
| `active` | Üye | ✅ Evet | Kullanıcı onayladı, tam üyelik |
| `rejected` | Reddedildi | ❌ Hayır | Kullanıcı reddet basıldı |
| `blocked` | Engellendi | ❌ Hayır | Admin tarafından engellendi |
| `inactive` | Pasif | ❌ Hayır | Kendi isteğiyle çıktı |

---

## 🔌 API Endpoints

### 1. List Pending Invitations
```bash
GET /api/v1/communities/invitations/pending/?user_id=123

Response:
{
  "success": true,
  "data": [
    {
      "community_id": "507f1f77bcf86cd799439011",
      "community_name": "Liderlik Topluluğu",
      "community_type": "TRAIT",
      "trait_name": "Lider",
      "invited_at": 1712000000,
      "harmony_level": 75
    },
    {
      "community_id": "507f1f77bcf86cd799439012",
      "community_name": "Kariyer Modülü",
      "community_type": "MODULE",
      "trait_name": "Kariyer",
      "invited_at": 1712000010,
      "harmony_level": 75
    }
  ],
  "count": 2
}
```

**Query Parameters:**
- `user_id` (required) - Kullanıcı ID

**Dönüş:**
- Array of pending invitations
- Her davetyie: community_id, name, type, invited_at

---

### 2. Approve/Reject Invitation
```bash
POST /api/v1/communities/507f1f77bcf86cd799439011/approve/

Request (ONAYLA):
{
  "user_id": 123,
  "action": "approve"
}

Response:
{
  "success": true,
  "data": {
    "community_id": "507f1f77bcf86cd799439011",
    "user_id": 123,
    "status": "active",
    "message": "Topluluğa başarıyla katıldınız!"
  }
}

---

Request (REDDET):
{
  "user_id": 123,
  "action": "reject"
}

Response:
{
  "success": true,
  "data": {
    "community_id": "507f1f77bcf86cd799439011",
    "user_id": 123,
    "status": "rejected",
    "message": "Davetiye reddedildi."
  }
}
```

---

## 🗄️ Database Schema Changes

### community_members Collection

**Önceki (Eski) Yapı:**
```javascript
{
  community_id: String,
  user_id: Number,
  joined_at: Timestamp,        // Hemen katıldığı zaman
  harmony_level: Number,
  is_mod: Boolean
}
```

**Yeni (Onay Sistemiyle) Yapı:**
```javascript
{
  community_id: String,
  user_id: Number,
  status: String,              // 🆕 pending | active | rejected | blocked
  invited_at: Timestamp,       // 🆕 Davet gönderme zamanı
  joined_at: Timestamp,        // Onay verme zamanı (null ise pending)
  approved_at: Timestamp,      // 🆕 Onay zamanı
  harmony_level: Number,
  is_mod: Boolean,
  reason_rejected: String      // 🆕 Reddediliş sebebi (opsiyonel)
}
```

**Indexes:**
```javascript
// Pending davetyileri hızlı bulmak
db.community_members.createIndex({
  "user_id": 1,
  "status": 1
})

// Topluluk üyelerini bulmak
db.community_members.createIndex({
  "community_id": 1,
  "status": 1
})
```

---

## 📱 User Interface Mockup

### Kullanıcı Dashboard

```
┌──────────────────────────────────────────────┐
│  Topluluk Davetiyeleriniz                   │
├──────────────────────────────────────────────┤
│                                              │
│ 📌 Liderlik Topluluğu                       │
│    "Lider" özelliğine davet edildiniz      │
│    [✅ ONAYLA]  [❌ REDDET]                 │
│                                              │
│ 📌 Kariyer Modülü                           │
│    "Kariyer" modülüne davet edildiniz      │
│    [✅ ONAYLA]  [❌ REDDET]                 │
│                                              │
│ 📌 Empatik Topluluğu                        │
│    "Empatik" özelliğine davet edildiniz    │
│    [✅ ONAYLA]  [❌ REDDET]                 │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🔒 KVKK/GDPR Compliance

### Neden Gerekli?

✅ **KVKK (Kişisel Verilerin Korunması Kanunu) Uyumluluğu**
- Madde 5: Veri işleme ilkeleri
- Madde 8: Özel nitelikli verilerin işlenmesi
- Madde 10: Rıza gereken durumlar

✅ **GDPR (Avrupa Veri Koruma Yönetmeliği)**
- Article 6: Lawful basis for processing
- Article 7: Conditions for consent
- Article 9: Processing of special categories

### Uyum Mekanizmaları

| Gereklilik | Uygulama |
|----------|----------|
| Açık rıza | Explicit approval button |
| Tarafsızlık | Same treatment for all users |
| Şeffaflık | Clear message about data usage |
| Kontrol | Easy to reject/withdraw |
| Belgeleme | Logs show when approval given |

---

## 🔐 Implementation Details

### Community Hooks (auto_add_to_communities)

**Eski Kod (❌ Yanlış):**
```python
members_col.insert_one({
    'status': 'active',  # ❌ Doğrudan aktif
    'joined_at': time.time()
})
```

**Yeni Kod (✅ Doğru):**
```python
members_col.insert_one({
    'status': 'pending',  # ✅ Bekleyiş durumu
    'invited_at': time.time(),
    'joined_at': None,
    'approved_at': None
})
```

### Message Sending (Phase 2)

**Direktçi Mesajlaşma Kuralları:**
```python
# Only UYUMLU + status='active' can message
if compatibility['category'] == 'UYUMLU':
    # Check if membership is active
    member = members_col.find_one({
        'user_id': to_user_id,
        'status': 'active'  # ✅ Sadece onaylı üyeler
    })
    
    if member:
        allow_message()  # ✅ İzin ver
    else:
        deny_message()   # ❌ Reddet
```

---

## 📋 Checklist

### Phase 1 Implementation
- [x] Pending status field added
- [x] Auto-add sends invitations (pending)
- [x] Approval endpoint created
- [x] Rejection endpoint created
- [x] Pending invitations list endpoint
- [x] Database schema updated
- [x] KVKK/GDPR compliance documented

### Phase 2 (Messaging)
- [ ] Message endpoints check for active status
- [ ] Direct messaging requires UYUMLU + active
- [ ] Block/mute functionality
- [ ] Message history only for active members

### Phase 3 (Groups)
- [ ] Group invitations use same pending system
- [ ] Group owner has authority to approve
- [ ] Member can leave anytime

---

## 🚀 Testing Scenarios

### Scenario 1: User Accepts Invitation
```
1. User completes analysis
2. Gets 5 pending invitations
3. Calls GET /invitations/pending/ → sees 5 invitations
4. Calls POST /approve/ with action=approve
5. Status changes: pending → active
6. Member count incremented
7. Can now access community chat
```

### Scenario 2: User Rejects Invitation
```
1. User gets pending invitation
2. Calls POST /approve/ with action=reject
3. Status changes: pending → rejected
4. Later, can get same invitation again
5. Or auto-invite only on new analysis
```

### Scenario 3: User Ignores Invitation
```
1. User gets pending invitations
2. Does not respond
3. Status stays: pending
4. Cannot access community (read-only preview)
5. Can accept/reject anytime later
```

---

## 📊 Analytics & Monitoring

### Metrics to Track

```
Acceptance Rate:
  Invitations sent / Approvals = %
  Target: >70%

Rejection Rate:
  Rejections / Invitations = %
  Target: <15%

Pending Duration:
  Average days until response
  Target: <3 days
```

### Logging

```python
# Log every approval/rejection
log.info(f'User {user_id} APPROVED community {community_id}')
log.info(f'User {user_id} REJECTED community {community_id}')

# Dashboard metrics
metrics = {
    'total_invitations': 1000,
    'approved': 750,
    'rejected': 150,
    'pending': 100
}
```

---

## 🔄 Future Enhancements

### Phase 2+

**Bulk Approval**
```bash
POST /api/v1/communities/invitations/bulk-approve/
{
  "user_id": 123,
  "action": "approve_all"  // Tüm davetyileri onayla
}
```

**Customizable Defaults**
```
User Settings:
  [ ] Auto-approve all TRAIT communities
  [ ] Auto-reject MODULE communities
  [ ] Ask for each invitation
```

**Reminder Notifications**
```
After 7 days of pending:
  - Send notification
  - "You have 3 pending invitations"
  - Link to approve/reject
```

---

## 📚 Documentation Links

- PHASE1_IMPLEMENTATION_PLAN.md — Overall plan
- PHASE1_DATABASE_SCHEMA.md — Collections structure
- PHASE1_QUICK_START.md — API usage

---

## ✅ Summary

✅ **What's Protected:**
- Community membership requires explicit approval
- Users cannot be added to communities without consent
- All changes logged and traceable
- KVKK/GDPR compliant

✅ **User Experience:**
- Simple approve/reject buttons
- See all pending invitations
- Can change mind anytime
- Clear notifications

✅ **Compliance:**
- Explicit user consent
- Transparent data handling
- User control maintained
- Audit trail available

---

**Status:** ✅ IMPLEMENTED  
**Compliance:** ✅ KVKK + GDPR Ready  
**Next Step:** Phase 2 Messaging (with same consent rules)
