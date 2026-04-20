# Chat Context Integration Guide

**Date:** 2026-04-14  
**Status:** Implementation Ready  
**Target:** FastAPI Chat Service (port 8002)

---

## 📋 Yapılacaklar Özeti

```
✅ ADIM 1: views.py - image_quality ekle (YAPILDI)
✅ ADIM 2: chat_context_builder.py - Context builder (YAPILDI)
✅ ADIM 3: setup_chat_context.py - MongoDB setup (YAPILDI)
✅ ADIM 4: ollama_system_prompt.py - Prompt template (YAPILDI)
⏳ ADIM 5: FastAPI Chat Service'i güncelle (SONRA YAPILACAK)
```

---

## 🔗 Entegrasyon Noktaları

### 1. Django → FastAPI Chat

**Mevcut Flow (Django'dan):**
```python
# analysis_api/views.py
result = _run_analysis(img_path, self.mode, lang, **extra)

# Yeni: image_quality'yi ekle (YAPILDI)
result['image_quality'] = {...quality metrics...}

# Cache'le (chat_context_builder'da)
cache_analysis_result(user_id, lang, result)

return JsonResponse({'success': True, 'data': result})
```

**Mobile → FastAPI Chat:**
```typescript
// ChatScreen.tsx
const analysisResult = route.params?.analysisResult ?? {}; // Django'dan gelen
await ChatAPI.startChat(analysisResult, lang);
```

**FastAPI Chat (TBD):**
```python
# /v1/chat/analyze endpoint
@app.post("/v1/chat/analyze")
async def start_chat(req: ChatStartRequest):
    user_id = get_user_id_from_token()
    
    # Adım 1: Context oluştur
    context = build_ollama_context(user_id, req.lang)
    
    # Adım 2: System prompt'u hazırla
    system_prompt = get_system_prompt(req.lang, context)
    
    # Adım 3: Ollama'ya gönder
    response = ollama.generate(
        model='mistral',
        system=system_prompt,
        prompt=f"Kullanıcının kişiliği: {context['user'].get('name')}"
    )
    
    # Adım 4: Conversation kaydet
    conversation_id = save_conversation(user_id, req.lang, context)
    
    return {
        'conversation_id': conversation_id,
        'assistant_message': response,
        'lang': req.lang
    }
```

---

## 📦 Import Yapıları

### Django Backend (views.py + chat_context_builder.py)

```python
# views.py'da
from analysis_api.chat_context_builder import (
    cache_analysis_result,
    build_ollama_context
)

# Analysis sonucu aldıktan sonra:
try:
    cache_analysis_result(user_id, lang, result)
except Exception as e:
    log.warning(f'Cache failed: {e}')
```

### FastAPI Chat Service

```python
# FastAPI'da
import sys
sys.path.insert(0, '/path/to/django/analysis_api')

from chat_context_builder import build_ollama_context
from ollama_system_prompt import get_system_prompt, get_context_summary
```

---

## 🗄️ MongoDB Collections

### Collection 1: analysis_cache

**Purpose:** analysisResult'ı 30 gün cache'le

```javascript
// Örnek document
{
  "_id": ObjectId("..."),
  "user_id": 123,
  "lang": "tr",
  "photo_hash": "abc123...",
  "result": {
    "face_detected": true,
    "golden_ratio": 1.618,
    "sifatlar": [...],
    "similarity": {...},
    "image_quality": {
      "overall_score": 85,
      "brightness": {...},
      "contrast": {...},
      "face_centering": {...}
    },
    ...
  },
  "created_at": 1713000000,
  "accessed_at": 1713001000
}
```

**Indexes:**
```
- (user_id, lang)
- (user_id, lang, photo_hash)
- created_at (TTL: 30 days)
- accessed_at (DESC)
```

### Collection 2: compatibility_cache

**Purpose:** Uyumluluğu 30 gün cache'le

```javascript
{
  "_id": ObjectId("..."),
  "user1_id": 123,
  "user2_id": 456,  // user1_id < user2_id (symmetry)
  "score": 85,
  "category": "UYUMLU",
  "can_message": true,
  "golden_ratio_diff": 0.0234,
  "sifat_overlap": 5,
  "module_overlap": 3,
  "conflict_count": 0,
  "result": {...full_result...},
  "created_at": 1713000000
}
```

**Indexes:**
```
- (user1_id, user2_id) UNIQUE
- (user1_id)
- (user2_id)
- created_at (TTL: 30 days)
- score (DESC)
```

### Collection 3: user_profiles

**Purpose:** User ↔ Partner mapping

```javascript
{
  "_id": ObjectId("..."),
  "user_id": 123,
  "partner_id": 456,  // optional
  "modules": ["kariyer", "liderlik"],
  "preferences": {
    "language": "tr",
    "notifications": true
  },
  "updated_at": 1713000000
}
```

**Indexes:**
```
- (user_id) UNIQUE
- (partner_id)
- updated_at (DESC)
```

---

## 🚀 Setup ve Deployment

### Step 1: MongoDB Collections Oluştur

```bash
cd facesyma_backend

# Django shell'de çalıştır
python manage.py shell

# Sonra
exec(open('setup_chat_context.py').read())
```

**Output:**
```
🔧 Setting up Chat Context Collections...

1️⃣  Creating analysis_cache collection...
   ✅ analysis_cache OK
   ...

✅ All collections created successfully!
```

### Step 2: Image Quality'yi Views'a Ekle

✅ **YAPILDI** - views.py'a image_quality eklemesi tamamlandı

Kontrol:
```bash
# Bir analiz yapıp log'ları kontrol et
python manage.py runserver

# Test request:
curl -X POST http://localhost:8000/api/v1/analysis/analyze/ \
  -F "image=@test.jpg" \
  -F "lang=tr"

# Response'da image_quality var mı?
# {"success": true, "data": {"image_quality": {...}}}
```

### Step 3: FastAPI Chat Service'i Güncelle

**Dosya:** `/path/to/chat_service/main.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys

# Django'ya erişim
sys.path.insert(0, '/path/to/django')
from analysis_api.chat_context_builder import (
    build_ollama_context,
    cache_analysis_result
)
from analysis_api.ollama_system_prompt import get_system_prompt

app = FastAPI()

class ChatStartRequest(BaseModel):
    analysis_result: dict
    lang: str = 'tr'
    first_message: str = None

class ChatMessageRequest(BaseModel):
    conversation_id: str
    message: str
    lang: str = 'tr'

# Ollama client (shimaya göre configure et)
import ollama
OLLAMA_MODEL = 'mistral'

# Conversation store (MongoDB veya Redis)
conversations = {}  # Temporary; use MongoDB in production

@app.post("/v1/chat/analyze")
async def start_chat(req: ChatStartRequest):
    try:
        # 1. analysisResult'ı cache'le
        user_id = get_user_id_from_token()  # JWT'den çıkar
        cache_analysis_result(user_id, req.lang, req.analysis_result)
        
        # 2. Context oluştur
        context = build_ollama_context(user_id, req.lang)
        
        # 3. System prompt hazırla
        system_prompt = get_system_prompt(req.lang, context)
        
        # 4. İlk mesaj
        first_prompt = req.first_message or "Beni tanı ve hangi yardım yapabileceğini söyle."
        
        # 5. Ollama'ya çağrı
        response = ollama.generate(
            model=OLLAMA_MODEL,
            system=system_prompt,
            prompt=first_prompt,
            stream=False
        )
        
        # 6. Conversation kaydet
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {
            'user_id': user_id,
            'lang': req.lang,
            'context': context,
            'messages': [
                {'role': 'assistant', 'content': response['response']}
            ],
            'created_at': time.time()
        }
        
        return {
            'conversation_id': conversation_id,
            'assistant_message': response['response'],
            'lang': req.lang
        }
    
    except Exception as e:
        log.exception(f'Chat start error: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/message")
async def send_message(req: ChatMessageRequest):
    try:
        # Conversation yükle
        conv = conversations.get(req.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # User mesajı ekle
        conv['messages'].append({
            'role': 'user',
            'content': req.message
        })
        
        # System prompt oluştur
        system_prompt = get_system_prompt(req.lang, conv['context'])
        
        # Conversation history'yi prompt'a ekle
        history_text = '\n'.join([
            f"{m['role'].upper()}: {m['content']}"
            for m in conv['messages'][-5:]  # Son 5 mesaj
        ])
        
        prompt = f"{history_text}\nASSISTANT:"
        
        # Ollama'ya çağrı
        response = ollama.generate(
            model=OLLAMA_MODEL,
            system=system_prompt,
            prompt=prompt,
            stream=False
        )
        
        # Asistan mesajı ekle
        conv['messages'].append({
            'role': 'assistant',
            'content': response['response']
        })
        
        return {
            'conversation_id': req.conversation_id,
            'assistant_message': response['response']
        }
    
    except Exception as e:
        log.exception(f'Chat message error: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📊 Monitoring & Stats

### Context Cache Hit Rate

```python
# chat_context_builder.py'da tracking
def log_context_stats(user_id: int, hit: bool, source: str = 'unknown'):
    """Monitoring için stats kaydedilir"""
    try:
        col = _get_db()['chat_context_stats']
        col.insert_one({
            'user_id': user_id,
            'hit': hit,
            'source': source,  # cache, api, compatibility
            'timestamp': time.time()
        })
    except Exception as e:
        log.warning(f'Stats logging failed: {e}')
```

### Dashboard Metrics

```
Daily:
- Cache hit rate (%)
- Avg context build time (ms)
- Compatibility pre-calc time (ms)
- TTL expiration rate
- User-partner ratio

Weekly:
- Top accessed users
- Compatibility check frequency
- Image quality distribution
```

---

## 🧪 Testing

### Unit Test: Context Builder

```python
# test_chat_context_builder.py
import pytest
from chat_context_builder import (
    cache_analysis_result,
    get_analysis_result,
    build_ollama_context
)

def test_cache_and_retrieve():
    """analysisResult'ı cache'le ve geri al"""
    user_id = 123
    lang = 'tr'
    analysis = {
        'name': 'Test User',
        'sifatlar': ['Lider', 'Meraklı'],
        'golden_ratio': 1.618,
        'image_quality': {'overall_score': 85}
    }
    
    # Cache'le
    cache_analysis_result(user_id, lang, analysis)
    
    # Geri al
    cached = get_analysis_result(user_id, lang)
    assert cached is not None
    assert cached['result']['name'] == 'Test User'
    assert cached['result']['image_quality']['overall_score'] == 85

def test_ollama_context_building():
    """Context'i başarıyla oluştur"""
    user_id = 123
    context = build_ollama_context(user_id, 'tr')
    
    assert context['user'] is not None
    assert context['user'].get('golden_ratio') > 0
    assert 'image_quality' in context['user']

def test_compatibility_context():
    """Partner varsa compatibility context'i ekle"""
    user_id = 123
    partner_id = 456
    
    # Setup: Partner data cache'le
    # ... setup code ...
    
    context = build_ollama_context(user_id, 'tr', partner_id)
    
    assert context['partner'] is not None
    assert context['compatibility'] is not None
    assert context['compatibility']['score'] > 0
```

### Integration Test: Chat API

```python
# test_chat_api.py
def test_chat_start_with_context():
    """Chat başlat ve context'i kontrol et"""
    analysis_result = {
        'name': 'John',
        'sifatlar': ['Lider'],
        'golden_ratio': 1.618,
        'image_quality': {'overall_score': 85}
    }
    
    response = client.post('/v1/chat/analyze', json={
        'analysis_result': analysis_result,
        'lang': 'tr'
    })
    
    assert response.status_code == 200
    assert 'conversation_id' in response.json()
    assert 'assistant_message' in response.json()
    assert len(response.json()['assistant_message']) > 0
```

---

## 📝 Checklist

- [ ] `setup_chat_context.py` çalıştırarak MongoDB collections oluştur
- [ ] `views.py`'daki image_quality entegrasyonunu doğrula
- [ ] FastAPI Chat Service'i chat_context_builder ile güncelle
- [ ] Ollama system prompt'unu uygulamasına ekle
- [ ] Unit tests çalıştır
- [ ] Integration tests çalıştır
- [ ] Production'a deploy et
- [ ] Monitoring & stats'ı kur
- [ ] User feedback topla

---

## 🔧 Troubleshooting

### Problem: "Connection refused" MongoDB

```
Çözüm: MongoDB URI'yi kontrol et (settings.py)
  MONGO_URI = 'mongodb+srv://...'
  Eğer local: 'mongodb://localhost:27017/'
```

### Problem: Ollama model yüklenmedi

```
Çözüm:
  ollama pull mistral
  ollama serve (ayrı terminal'de)
```

### Problem: Cache miss sık oluyor

```
Çözüm: TTL'i arttır veya cache cleanup'ı optime et
  current: 30 days (2592000 seconds)
  önerilen: 60 days (5184000 seconds) high-traffic için
```

---

**Status: Ready for FastAPI implementation** 🚀
