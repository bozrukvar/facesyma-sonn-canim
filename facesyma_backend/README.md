# Facesyma Backend — Django REST API

## Kurulum

```bash
pip install -r requirements.txt
```

## Yapılandırma

`.env.example` dosyasını `.env` olarak kopyala ve doldur:

```bash
cp .env.example .env
```

Zorunlu değerler:
```
DJANGO_SECRET_KEY=...
MONGO_URI=mongodb+srv://...
JWT_SECRET=...
GOOGLE_CLIENT_ID=...
FACESYMA_ENGINE_PATH=/sunucudaki/facesyma_revize/yolu
```

## Çalıştırma

```bash
# Geliştirme
python manage.py runserver 0.0.0.0:8000

# Production
gunicorn facesyma_project.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Docker
docker build -t facesyma-backend .
docker run -p 8000:8000 --env-file .env facesyma-backend
```

## Endpoint'ler

### Auth `/api/v1/auth/`
| Method | URL | Açıklama |
|--------|-----|---------|
| POST | `/register/` | Email ile kayıt |
| POST | `/token/` | Email ile giriş → JWT |
| POST | `/token/refresh/` | Token yenile |
| POST | `/google/` | Google OAuth |
| GET/PATCH | `/me/` | Profil |

### Analysis `/api/v1/analysis/`
| Method | URL | Açıklama |
|--------|-----|---------|
| POST | `/analyze/` | Temel karakter analizi |
| POST | `/analyze/modules/` | 13 modül (kariyer, müzik, ...) |
| POST | `/analyze/golden/` | Altın oran |
| POST | `/analyze/face_type/` | Yüz tipi |
| POST | `/analyze/art/` | Sanat eşleşmesi |
| POST | `/analyze/astrology/` | Astroloji |
| POST | `/twins/` | 2-5 kişi uyum |
| GET  | `/history/` | Analiz geçmişi |
| GET  | `/daily/` | Günlük motivasyon |

## Sunucu Dizin Yapısı

```
/home/facesymagroups/facesyma-backend/
├── facesyma_revize/       ← Yüz analiz motoru (mevcut)
├── facesyma_backend/      ← Bu Django projesi
│   ├── manage.py
│   ├── facesyma_project/
│   ├── analysis_api/
│   ├── auth_api/
│   └── .env
```

`FACESYMA_ENGINE_PATH` değişkeni `facesyma_revize` klasörünün tam yolunu göstermelidir.
