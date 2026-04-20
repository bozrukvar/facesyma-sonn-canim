# Ollama LLM Context Architecture - Analiz Raporu

**Date:** 2026-04-14  
**Status:** Inceleme Tamamlandı - Eksikleri Tespit Edildi  
**Critical Finding:** ✅ Chat API var, ancak context'e hangi data ekleniyor - TESPİT GEREKLI

---

## 1. Coach API & Chat API - MEVCUT

### Mimari Şema
```
Mobile App
  ├─ ChatScreen
  │  ├─ analysisResult (ne eklenediği?)
  │  └─ ChatAPI.startChat(analysisResult, lang)
  │
  ├─ CoachAPI.analyzeWithCoach(analysisResult, lang, modules)
  │
  └─ Services (API)
     ├─ analysisClient → http://localhost:8000/api/v1/analysis (Django)
     ├─ chatClient → http://localhost:8002/v1/chat (FastAPI) ← AI Chat
     └─ coachClient → http://localhost:8003/coach (FastAPI) ← Coach
```

### Kod Evidence:

**ChatScreen.tsx (line 105-106):**
```typescript
const analysisResult = route.params?.analysisResult ?? {};
// ← AnalysisScreen'den gelen veri
```

**AnalysisScreen.tsx (line 195-196):**
```typescript
navigation.navigate('Chat', { analysisResult: result, lang })
// ← 'result' ne içeriyor? Sadece character analysis mi?
```

**api.ts (line 224-228):**
```typescript
export const ChatAPI = {
  startChat: async (analysisResult: object, lang = 'tr', firstMessage?: string) => {
    const res = await aiChatAxios.post('/v1/chat/analyze', {
      analysis_result: analysisResult,  // ← Bu nesne Ollama'ya gidiyor
      lang, 
      first_message: firstMessage,
    });
  }
}
```

---

## 2. analysisResult NEYİ İÇERİYOR?

### Current State (Django'dan dönen):
```python
# views.py (_run_analysis fonksiyonundan)
result = {
  'face_detected': bool,
  'age_group': str,
  'gender': str,
  'golden_ratio': float,
  'attributes': [...],
  'sifatlar': [...],        # ✅ 201 sıfat
  'kariyer': str,
  'liderlik': str,
  'daily': str,
  'similarity': {            # ✅ Phase 1 eklendi
    'celebrities': [...],
    'historical': [...],
    'objects': [...],
    'plants': [...],
    'animals': [...],
    'summary': str
  },
  '_community_join': {...}   # ✅ Phase 1 eklendi
}
```

### EKSIK: Compatibility
```python
# ❌ COMPATIBILITY RESULT EKLENME İYORMU?
# Twins endpoint'i ayrı: /api/v1/analysis/twins/
# AnalysisScreen'den erişiliyor mu?

# ❌ Kontrol: AnalysisScreen'de Compatibility var mı?
# Cevap: YOK - Twins analizi ayrı endpoint
```

---

## 3. LLM Context Flow Analizi

### Chat API'ye Giden Veri:
```
AnalysisScreen (result)
  ├─ ✅ Character analysis (sifatlar, attributes)
  ├─ ✅ Golden ratio
  ├─ ✅ Face type (age, gender)
  ├─ ✅ Similarity (5 Benzeriniz)
  ├─ ✅ Modules (kariyer, liderlik, daily)
  ├─ ✅ Community (auto-join bilgisi)
  │
  └─ ❌ Compatibility (EKSIK)
     - Twins endpoint ayrı
     - User profile'dan çekilmiyor
     - Context'e eklenmemiş
```

### Coach API'ye Giden Veri:
```
CoachAPI.analyzeWithCoach(analysisResult, lang, modules)
  ├─ analysisResult (üstteki aynı)
  └─ include_modules: ['kariyer', 'liderlik', ...] (opsiyonel)
```

---

## 4. OLLAMA'YA PROBLEM

### Şu Anda Ollama Biliyor:
- ✅ User'ın sifatları (201 sıfat)
- ✅ Golden ratio
- ✅ Face type
- ✅ 5 Benzeriniz (similarity)
- ✅ Kariyer/Liderlik/Daily modules
- ✅ Community membership

### OLLAMA BİLMİYOR:
- ❌ Compatibility (uyumluluğu) - **KRITIK EKSIK**
  - User + Partner bilgileri
  - Uyum skoru
  - Sifat overlap'i
  - Module overlap'i

- ❌ Image quality metrics
  - Brightness/Contrast/Face centering
  - Quality score

- ❌ Multi-user scenario'ları
  - Eğer partner data varsa, nasıl sunulur?

---

## 5. CONTEXT NASIL OLUŞTURULUYOR?

### Option A: Real-time (Mevcut)
```
User upload fotoğraf
  → AnalysisScreen: /analyze/ endpoint çağır
  → Result al (character + similarity)
  → ChatScreen'e geç
  → Chat API'ye analysisResult gönder
  → FastAPI Ollama'ya gönder
  → Ollama yanıt ver
```

**Avantaj:** Fresh, up-to-date data  
**Dezavantaj:** Compatibility data yok

### Option B: History'den (Önerilen Yeni)
```
User chat başlat
  → History API'den user'ın önceki analiz sonuçlarını çek
  → Compatibility check: partner analizi var mı?
  → Context'e ekle: analysis + similarity + compatibility
  → Chat API'ye gönder
```

**Avantaj:** Complete context  
**Dezavantaj:** Eski veri olabilir

### Option C: Caching (İleri)
```
User upload fotoğraf
  → MongoDB'de analysisResult cache'le
  → Compatibility check otomatik (eğer partner varsa)
  → 30-day TTL

Sonraki sorgularda:
  → Cache'den oku (hızlı)
  → Fresh data varsa update et
```

---

## 6. Multi-User Scenario (Compatibility)

### Şu anki durum:
```
User A fotoğraf çeker
  → /analyze/ → result_A al
  → Chat başlat: "Ben hakkında anlat"
  → Ollama: result_A'dan yanıt ver ✅

User B'yle uyumluluğu sorgula:
  → "B'yle uyumluyuz?" diye sor
  → Ollama'da B'nin data'sı YOK ❌
  → Context'te sadece result_A var
```

### Çözüm Gerekli:
```
User A Chat'te: "B'yle uyumluluğumuzu kontrol et"
  → Backend: B'nin user_id'sini al
  → MongoDB'den B'nin son analysisResult'ını çek
  → Compatibility check: /compatibility/check/
  → Result'ı Ollama context'ine ekle
  → Ollama: "Sizin uyum skoru 85, çünkü..."
```

---

## 7. Image Quality Metrics - OLLAMA'YA LAZIM MI?

### Bağlamı:
```
User: "Neden kalite skorum düşük çıktı?"
Ollama: ❌ "Bilmiyorum, kalite metrics'ine erişemiyorum"
```

### Çözüm:
```
Analysis result'a ekle:
{
  ...
  'image_quality': {
    'overall_score': 85,
    'brightness': {'value': 150, 'score': 100},
    'contrast': {'value': 65, 'score': 85},
    'face_centering': {'offset': 10, 'score': 90}
  }
}
```

---

## 8. Caching Strategy

### Mevcut:
```
AnalysisScreen
  └─ result = await AnalysisAPI.analyze(imageUri, lang)
     (Her seferinde hesaplanıyor)
```

### Önerilen:
```
AnalysisScreen
  └─ result = await AnalysisAPI.analyze(imageUri, lang)
     // MongoDB'de analysisResult TTL cache'le
     // user_id + lang + photo_hash key'e
     // 30-day expiry

ChatScreen
  ├─ analysis = getFromCache(user_id)
  ├─ compatibility = getCompatibility(user_id, partner_id) [IF EXISTS]
  ├─ image_quality = analysis['image_quality']
  └─ Ollama context'e ekle
```

---

## 9. ÖZET - Ne Eksik?

| Feature | Status | Ollama'ya Gidiyor? | Gerekli? |
|---------|--------|---|---|
| Character Analysis | ✅ Var | ✅ Evet | ✅ Kritik |
| Similarity (5 Benzeriniz) | ✅ Var | ✅ Evet | ✅ Kritik |
| Golden Ratio | ✅ Var | ✅ Evet | ✅ Önemli |
| Face Type | ✅ Var | ✅ Evet | ✅ Önemli |
| Modules (Kariyer/Liderlik) | ✅ Var | ✅ Evet | ✅ Önemli |
| **Compatibility** | ✅ Var (API) | ❌ **HAYIR** | ✅ **KRITIK** |
| **Image Quality** | ✅ Var (Utils) | ❌ **HAYIR** | ⚠️ Faydalı |
| Community | ✅ Var | ✅ Evet | ⚠️ Faydalı |

---

## 10. IMPLEMENTATION PLAN

### Phase 1: Compatibility Entegrasyonu
```
1. AnalysisScreen: result'a compatibility ekle
   - Eğer user'ın partner_id varsa
   - /compatibility/check/ call et
   - Result'a ekle

2. ChatAPI: analysisResult'ta compatibility'yi bekle
   - Ollama prompt'unu güncelle
   - Compatibility context'i document et

3. CoachAPI: Aynısını yap
```

### Phase 2: Image Quality Metrics
```
1. views.py: analysis result'ına image_quality ekle
2. imageQuality.ts: kullan (mobile'de zaten var)
3. Ollama prompt: quality metrics'i açıkla
```

### Phase 3: Caching & Optimization
```
1. analysisResult MongoDB cache'le
2. Compatibility cache'le
3. Multi-user context efficiently handle et
```

---

## 🎯 SONUÇ

**Coach/Chat API'si MEVCUT** ✅
- FastAPI (port 8002, 8003)
- analysisResult context'i gönderiliyor

**EKSIK OLAN:**
1. **Compatibility data** - API var ama context'e eklenmemiş
2. **Image quality metrics** - Backend'de var ama context'e eklenmemiş
3. **Caching strategy** - Optimize edilmemiş

**SONRAKİ ADIMLAR:**
1. Compatibility'yi Chat context'e ekle
2. Image quality'yi result'a ekle
3. Caching stratejisi oluştur
4. Ollama prompt'unu güncelle

---

**Ready for implementation planning** 🚀
