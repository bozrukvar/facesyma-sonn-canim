# Facesyma Yaşam Koçu Modülü

Mevcut 201 sıfat veritabanını **14 yeni koçluk modülüyle** genişletir.
Tüm veriler **ayrı bir backup veritabanına** yazılır — mevcut `facesyma-backend`'e dokunulmaz.

---

## Yeni Modüller (14 adet)

| Modül | Açıklama |
|-------|---------|
| `saglik_esenwlik` | Sağlıklı Yaşam ve Esenlik |
| `dogruluk_sadakat` | Doğruluk ve Sadakat |
| `guvenlik` | Güvenlik Profili (kişisel, duygusal, finansal) |
| `suc_egilim` | Risk / Suç Eğilim Analizi (etik çerçevede) |
| `iliski_yonetimi` | İlişki Yönetimi |
| `iletisim_becerileri` | İletişim Becerileri |
| `stres_yonetimi` | Stres ve Zaman Yönetimi |
| `ozguven` | Özgüven Artırma |
| `zaman_yonetimi` | Zaman Yönetimi |
| `kisisel_hedefler` | Kişisel Gelişim Hedefleri |
| `astroloji_harita` | Astroloji Haritası & Yorumları |
| `dogum_analizi` | Doğum Tarihi/Saati Analizi + Numeroloji |
| `yas_koc_ozet` | Yaşam Koçu Genel Özeti |
| `vucut_dil` | Beden Dili Analizi (yüz verisinden) |

---

## Veritabanı Mimarisi

```
facesyma-backend          ← DOKUNULMAZ (mevcut)
  └─ database_attribute_tr/en/...
  └─ appfaceapi_myuser
  └─ ...

facesyma-coach-backup     ← YENİ (sadece buraya yazılır)
  └─ coach_attributes_tr  (201 sıfat × 27 modül)
  └─ coach_attributes_en
  └─ coach_attributes_de
  └─ ... (18 dil)
  └─ coach_users          (kullanıcı koçluk profili)
  └─ coach_birth_data     (astroloji cache)
  └─ coach_sessions       (koç oturum geçmişi)
  └─ coach_goals          (kişisel hedef takibi)
```

---

## Adım Adım Kurulum

### 1. Bağımlılıkları Kur
```bash
pip install -r requirements.txt
```

### 2. Veri Setini Üret (Türkçe)
```bash
cd dataset
python generate_coach_dataset.py \
  --input  ../../facesyma_migrate/sifat_veritabani.json \
  --output sifat_coach_tr.json \
  --lang   tr
```

### 3. Tüm Diller (18 dil)
```bash
python generate_coach_dataset.py \
  --input  ../../facesyma_migrate/sifat_veritabani.json \
  --all-langs
```

### 4. Backup DB'ye Yaz
```bash
# Önce index'leri oluştur
cd ../migration
python setup_backup_db.py --create-indexes

# Türkçe migrate
python setup_backup_db.py --migrate --lang tr --source-dir ../dataset

# Tüm diller
python setup_backup_db.py --migrate --all-langs --source-dir ../dataset

# Doğrula
python setup_backup_db.py --verify
```

### 5. Ya da tek komutla (üret + yaz)
```bash
cd dataset
python generate_coach_dataset.py \
  --input  ../../facesyma_migrate/sifat_veritabani.json \
  --all-langs \
  --push-mongo
```

### 6. API'yi Başlat
```bash
cd api
uvicorn coach_api:app --host 0.0.0.0 --port 8003
```

---

## API Endpoint'leri

```
GET  /coach/modules              → 14 koç modülü listesi
POST /coach/profile              → Kullanıcı koç profili oluştur
GET  /coach/profile/{user_id}    → Kullanıcı profilini getir
POST /coach/analyze              → Analiz + koç yorumu üret
GET  /coach/sifat/{sifat}/{mod}  → Tekil sıfat + modül verisi
POST /coach/birth                → Doğum tarihi astroloji hesapla
GET  /coach/goals/{user_id}      → Kişisel hedefler
POST /coach/goals                → Yeni hedef ekle
PUT  /coach/goals/{goal_id}      → Hedef güncelle
GET  /languages                  → 18 dil listesi
GET  /health
```

---

## Doğum Tarihi / Saati Kullanımı

```bash
# Astroloji hesapla
curl -X POST http://localhost:8003/coach/birth \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1990-05-15","birth_time":"14:30","lang":"tr"}'
```

Dönen veri:
```json
{
  "astrology": {
    "sun_sign": "Boğa",
    "element":  "Toprak",
    "quality":  "Sabit",
    "season":   "İlkbahar",
    "time_energy": "Sosyal ve işbirlikçi"
  },
  "numerology": {
    "life_path_number": 7,
    "life_path_meaning": "Analist, mistik, içe dönük"
  }
}
```

---

## Desteklenen Diller (18)

tr 🇹🇷  en 🇬🇧  de 🇩🇪  ru 🇷🇺  ar 🇸🇦  es 🇪🇸  ko 🇰🇷  ja 🇯🇵
zh 🇨🇳  hi 🇮🇳  fr 🇫🇷  pt 🇧🇷  bn 🇧🇩  id 🇮🇩  ur 🇵🇰  it 🇮🇹  vi 🇻🇳  pl 🇵🇱

---

## Dosya Yapısı

```
facesyma_coach/
├── dataset/
│   └── generate_coach_dataset.py   # 14 modül veri üreticisi
├── migration/
│   └── setup_backup_db.py          # Backup DB kurulum + migrasyon
├── api/
│   └── coach_api.py                # FastAPI endpoint'leri
├── requirements.txt
└── README.md
```
