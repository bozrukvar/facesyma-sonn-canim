# 🚀 FACESYMA KURULUM VE TEST PLANI

> ⏱️ **Tahmini Süre:** 2-4 saat (her adım 15-30 dakika)  
> 🎯 **Hedef:** Projeyi adım adım test etmek ve her componentini doğrulamak

---

## 📋 İçindekiler
1. [Gereksinimler](#gereksinimler)
2. [Proje Yapısı](#proje-yapısı)
3. [Adım 1: Ortam Hazırlığı](#adım-1-ortam-hazırlığı)
4. [Adım 2: Backend Kurulumu](#adım-2-backend-kurulumu)
5. [Adım 3: Frontend Kurulumu](#adım-3-frontend-kurulumu)
6. [Adım 4: Test Endpoints](#adım-4-test-endpoints)
7. [Adım 5: İleri Özellikler](#adım-5-ileri-özellikler)

---

## 🛠️ Gereksinimler

### Kurulu Olması Gerekenler
- ✅ **Python 3.11+** → `python --version`
- ✅ **Node.js 18+** → `node --version`
- ✅ **pip** → `pip --version`
- ✅ **npm** → `npm --version`
- ✅ **Git** → `git --version`

### Opsiyonel (İleri Testler için)
- Docker (AI servisi için)
- Anthropic API Key (Claude çatı için)
- Android Studio (mobil emülatör için)

### MongoDB
- ✅ **MongoDB Atlas Cloud** VEYA
- ✅ **Local MongoDB** (`mongod` servisi)

---

## 📁 Proje Yapısı

```
facesyma-sonn-canim/
├── facesyma_backend/           ← Django REST API (Port 8000)
│   ├── manage.py
│   ├── requirements.txt
│   └── facesyma_project/
│
├── facesyma_mobile/            ← React Native (iOS/Android)
│   ├── package.json
│   └── src/
│
├── facesyma_ai/                ← AI Chat Service (Port 8002)
│   ├── requirements.txt
│   └── chat_service/
│
├── facesyma_coach/             ← Coaching API (Port 8003)
│   ├── requirements.txt
│   └── api/
│
├── facesyma_finetune/          ← LLM Fine-tuning
│   ├── requirements.txt
│   ├── dataset/
│   ├── training/
│   └── serving/
│
├── facesyma_migrate/           ← Data Migration
│   ├── sifat_veritabani.json   ← ✅ YENİ! (Excel'den dönüştürülmüş)
│   └── requirements.txt
│
└── SETUP_PLAN.md               ← Bu dosya
```

---

## ✏️ Adım 1: Ortam Hazırlığı

### 1.1 Gerekli Paketleri Yükle

```bash
# Proje klasörüne gir
cd c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim

# Tüm Python modüllerini yükle (global)
pip install --upgrade pip
pip install python-dotenv openpyxl pandas django djangorestframework pymongo PyJWT
```

### 1.2 `.env` Dosyasını Oluştur

```bash
# Backend .env
cd facesyma_backend
cat > .env << 'EOF'
DJANGO_SECRET_KEY=your-secret-key-dev-only-change-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,10.0.2.2
MONGO_URI=mongodb://localhost:27017/facesyma-backend
JWT_SECRET=your-jwt-secret-dev-only
JWT_ACCESS_EXP_HOURS=1
JWT_REFRESH_EXP_DAYS=30
GOOGLE_CLIENT_ID=your-google-client-id-here
FACESYMA_ENGINE_PATH=../facesyma_revize
UPLOAD_TMP=media/tmp
EOF
cd ..
```

### 1.3 MongoDB Başlat

```bash
# Option A: MongoDB Atlas (Cloud) kullanıyorsan
# MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/facesyma-backend

# Option B: Local MongoDB
mongod --dbpath "C:\data\mongodb"  # Ayrı terminal'de

# Bağlantıyı Test Et
python << 'EOF'
from pymongo import MongoClient
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB bağlantı OK")
except Exception as e:
    print(f"❌ MongoDB Hatası: {e}")
EOF
```

---

## 🔧 Adım 2: Backend Kurulumu

### 2.1 Django Bağımlılıkları

```bash
cd facesyma_backend

# requirements.txt'i kontrol et ve yükle
pip install -r requirements.txt

# Alternatif (tüm bağımlılıklar):
pip install \
  django==4.2.16 \
  djangorestframework==3.15.2 \
  django-cors-headers==4.4.0 \
  pymongo==4.7.2 \
  PyJWT==2.9.0 \
  google-auth==2.35.0 \
  Pillow==10.4.0 \
  numpy==1.26.4 \
  opencv-python-headless==4.10.0.84 \
  pandas==2.2.2

cd ..
```

### 2.2 Django Sunucusunu Başlat

```bash
cd facesyma_backend

# Geliştirme sunucusu
python manage.py runserver 0.0.0.0:8000

# Başarılı çıktı:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

✅ **Backend Çalışıyor:** `http://localhost:8000`

---

## 🧪 Adım 3: Backend API Test

### 3.1 Kullanıcı Kaydı

```bash
# Terminal açıp HTTP isteği gönder
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
  }'

# Beklenen Yanıt:
# {
#   "access": "eyJ0eXAi...",
#   "refresh": "eyJ0eXAi...",
#   "user": {
#     "id": 1,
#     "email": "test@example.com",
#     "name": "Test User",
#     "plan": "free",
#     "created_at": "2025-04-09T..."
#   }
# }
```

### 3.2 Giriş Yap (JWT Token Al)

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Token'ı kaydet (sonraki isteklerde kullan)
export TOKEN="eyJ0eXAi..."  # Gerçek token'ı yapıştır
```

### 3.3 Profil Getir

```bash
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer $TOKEN"

# ✅ Çalışmıyor mu? Token formatını kontrol et:
# Authorization: Bearer <token_buraya>
```

### 3.4 Günlük Motivasyon

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/daily/?lang=tr"

# Yanıt:
# {
#   "title": "Günün Mesajı",
#   "content": "..."
# }
```

---

## 📱 Adım 4: Mobile Kurulumu (React Native)

### 4.1 Dependencies Yükle

```bash
cd facesyma_mobile

# Node modules kur
npm install

# Beklenen çıktı:
# added 1000+ packages in 2m
```

### 4.2 API URL'lerini Güncelle

```bash
# src/services/api.ts dosyasını aç
# DEV_SERVICES URL'lerini kontrol et:
# analysis: 'http://10.0.2.2:8000/api/v1/analysis'  ← Android emülatör
# auth: 'http://10.0.2.2:8000/api/v1/auth'
```

### 4.3 Android Emülatörde Çalıştır

```bash
# Terminal 1: Metro bundler
npm start

# Terminal 2: Android'e deploy
npm run android

# Beklenen çıktı:
# ✅ Metro bundler açılıp, Android emülatörde app başlaması
```

### 4.4 iOS Çalıştırmak (macOS Gerekli)

```bash
# iOS dependencies
cd ios
pod install
cd ..

# Start
npm run ios
```

---

## 🔌 Adım 5: Test Araçları

### 5.1 Postman/Insomnia ile Test

**Insomnia Kurulumu:**
```bash
# https://insomnia.rest/download adresinden indir
# Veya: chocolatey ile
choco install insomnia
```

**Koleksiyon İçe Aktar:**
1. Insomnia açıl
2. `Create` → `Request Collection`
3. Aşağıdaki endpoint'leri ekle:

```json
{
  "name": "Facesyma API",
  "requests": [
    {
      "method": "POST",
      "url": "http://localhost:8000/api/v1/auth/register/",
      "body": {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test"
      }
    },
    {
      "method": "GET",
      "url": "http://localhost:8000/api/v1/auth/me/",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  ]
}
```

### 5.2 Python Test Script

```bash
# test_api.py oluştur
cat > test_api.py << 'EOF'
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Kullanıcı Kaydı
print("🧪 Test 1: Kullanıcı Kaydı")
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "email": "test@example.com",
    "password": "testpass123",
    "name": "Test User"
})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

# Test 2: Giriş Yap
if response.status_code == 201:
    print("🧪 Test 2: Giriş Yap")
    login_response = requests.post(f"{BASE_URL}/auth/token/", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    token = login_response.json().get("access")
    print(f"Token: {token[:20]}...\n")
    
    # Test 3: Profil
    print("🧪 Test 3: Profil Getir")
    headers = {"Authorization": f"Bearer {token}"}
    profile = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
    print(f"Profil: {json.dumps(profile.json(), indent=2, ensure_ascii=False)}\n")

# Test 4: Günlük Motivasyon
print("🧪 Test 4: Günlük Motivasyon")
daily = requests.get(f"{BASE_URL}/analysis/daily/?lang=tr")
print(f"Status: {daily.status_code}")
if daily.status_code == 200:
    print(f"✅ Motivasyon alındı!\n")
else:
    print(f"❌ Hata: {daily.text}\n")

EOF

python test_api.py
```

**Beklenen Çıktı:**
```
🧪 Test 1: Kullanıcı Kaydı
Status: 201
Response: {
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi...",
  "user": {...}
}

🧪 Test 2: Giriş Yap
Token: eyJ0eXAiOiJKV1...

🧪 Test 3: Profil Getir
Profil: {
  "id": 1,
  "email": "test@example.com",
  ...
}

🧪 Test 4: Günlük Motivasyon
Status: 200
✅ Motivasyon alındı!
```

---

## 🚀 Adım 6: İleri Testler (Opsiyonel)

### 6.1 AI Chat Service (Claude API)

**Gerekli:** Anthropic API Key

```bash
cd facesyma_ai

# .env oluştur
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
MONGO_URI=mongodb://localhost:27017/facesyma-backend
JWT_SECRET=your-jwt-secret
EOF

# Bağımlılıkları yükle
pip install -r requirements.txt

# FastAPI sunucusu başlat
python -m uvicorn chat_service.main:app --host 0.0.0.0 --port 8002 --reload
```

**Test:**
```bash
curl -X POST http://localhost:8002/chat/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "analysis_result": {
      "attributes": {"güvenilir": 0.95, "yaratıcı": 0.87}
    },
    "lang": "tr"
  }'
```

### 6.2 Coaching API

```bash
cd facesyma_coach

# .env oluştur (facesyma_ai ile aynı)
pip install -r requirements.txt

# FastAPI başlat
python -m uvicorn api.coach_api:app --host 0.0.0.0 --port 8003 --reload
```

**Test:**
```bash
curl -X GET http://localhost:8003/coach/modules
```

### 6.3 Yüz Analizi (Opsiyonel)

**Gerekli:** facesyma_revize motoru (dış bağımlılık)

```bash
# facesyma_revize klasörü setup (belgede yok - kendi sağlamalı)
# Ardından:

python << 'EOF'
import sys
sys.path.insert(0, '../facesyma_revize')

# Test analiz motoru
# (facesyma_revize API'sine bağlı)
EOF
```

---

## 📊 Adım 7: Veri Migration

### 7.1 Sifat Veritabanı (Excel → JSON)

✅ **TAMAMLANDI!** JSON dosyası oluşturuldu:
- 📁 Yolu: `facesyma_migrate/sifat_veritabani.json`
- 📊 İçerik: 201 sıfat × 30 cümle = 6,030 cümle
- 📦 Boyut: ~915 KB

### 7.2 MongoDB'ye Yükle

```bash
cd facesyma_migrate

cat > load_to_mongodb.py << 'EOF'
import json
from pymongo import MongoClient

# Bağlan
client = MongoClient("mongodb://localhost:27017/")
db = client["facesyma-backend"]
col = db["sifat_veritabani"]

# JSON yükle
with open("sifat_veritabani.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Sıfatları MongoDB'ye ekle
sifatlar = data.get("sifatlar", {})
for key, sifat in sifatlar.items():
    col.insert_one(sifat)

print(f"✅ {len(sifatlar)} sıfat MongoDB'ye yüklendi!")

# Kontrol
count = col.count_documents({})
print(f"   Toplam dokuman: {count}")

EOF

python load_to_mongodb.py
```

---

## ✅ KONTROL LİSTESİ

Aşağıdaki checklist'i tamamlayarak ilerleme takip et:

### Setup Aşaması
- [ ] Python 3.11+ yüklü
- [ ] Node.js 18+ yüklü
- [ ] MongoDB çalışıyor
- [ ] `.env` dosyaları oluşturuldu
- [ ] Tüm pip packages yüklü

### Backend
- [ ] Django sunucusu başlatıldı (Port 8000)
- [ ] Kullanıcı kaydı çalışıyor
- [ ] Giriş yapılabiliyor
- [ ] JWT token alınabiliyor
- [ ] Profil endpoint'i çalışıyor
- [ ] Günlük motivasyon endpoint'i çalışıyor

### Mobile (Opsiyonel)
- [ ] npm dependencies yüklü
- [ ] API URL'leri güncellendi
- [ ] Android emülatörde başladı VEYA iOS simulator'de

### AI Services (Opsiyonel)
- [ ] Chat API (FastAPI :8002) çalışıyor
- [ ] Coaching API (FastAPI :8003) çalışıyor
- [ ] Chat endpoint'leri test edildi

### Data
- [ ] sifat_veritabani.json oluşturuldu
- [ ] MongoDB'ye sıfatlar yüklendi

---

## 🐛 TROUBLESHOOTING

### Problem: MongoDB Bağlantısı Başarısız

```bash
# Çözüm 1: Kontrol et (localhost)
mongod --version

# Çözüm 2: Başlat
mongod --dbpath "C:\data\mongodb"

# Çözüm 3: Uzak sunucu (Atlas)
# .env'de doğru MONGO_URI kullan
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/database
```

### Problem: Port 8000 Zaten Kullanılıyor

```bash
# Çözüm: Farklı port kullan
python manage.py runserver 0.0.0.0:9000

# VEYA: Port'u boşalt
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Problem: JWT Token Hatası

```bash
# Kontrol et:
# 1. Token format: "Bearer <token>"
# 2. Authorization header doğru mu?
# 3. JWT_SECRET .env'de tanımlı mı?

# Debug:
python << 'EOF'
import jwt
token = "eyJ0..."
try:
    decoded = jwt.decode(token, "your-jwt-secret", algorithms=["HS256"])
    print(f"✅ Valid: {decoded}")
except Exception as e:
    print(f"❌ Invalid: {e}")
EOF
```

### Problem: CORS Hatası (Mobil)

```bash
# Django'da zaten çözüldü, fakat kontrol et:
# facesyma_project/settings.py

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://10.0.2.2:8000",  # Android emülatör
]
```

---

## 📞 NEXT STEPS

Setup tamamlandıktan sonra:

1. **Unit Tests Yaz**
   ```bash
   pip install pytest pytest-django
   pytest facesyma_backend/
   ```

2. **API Dökümentasyonu (Swagger)**
   ```bash
   pip install drf-spectacular
   # Django'da etkinleştir
   ```

3. **Docker ile Deployment**
   ```bash
   cd facesyma_backend
   docker build -t facesyma-backend .
   docker run -p 8000:8000 --env-file .env facesyma-backend
   ```

4. **LLM Fine-tuning (İleri)**
   ```bash
   cd facesyma_finetune
   python training/train.py --dataset ./dataset/dataset.jsonl
   ```

---

## 📚 REFERANSLAR

- [Django Documentation](https://docs.djangoproject.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Native Docs](https://reactnative.dev/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [JWT Basics](https://jwt.io/)

---

**Son Güncelleme:** 2025-04-09  
**Durum:** ✅ Setup Planı Hazır
