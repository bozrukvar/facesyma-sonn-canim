"""
facesyma_coach/api/coach_api.py
================================
Yaşam Koçu API — backup DB üzerinden çalışır.

Endpoint'ler:
  GET  /coach/modules              → Desteklenen koç modülleri
  POST /coach/profile              → Kullanıcı koç profili oluştur/güncelle
  GET  /coach/profile/{user_id}    → Kullanıcı profilini getir
  POST /coach/analyze              → Analiz + koç yorumu üret
  GET  /coach/sifat/{sifat}/{mod}  → Belirli sıfat + modül verisi
  POST /coach/giyim                → Kişiselleştirilmiş giyim tavsiyesi
  POST /coach/birth                → Doğum tarihi/saati astroloji hesapla
  GET  /coach/goals/{user_id}      → Kişisel hedefler
  POST /coach/goals                → Yeni hedef ekle
  PUT  /coach/goals/{goal_id}      → Hedef güncelle
  GET  /languages                  → 18 dil listesi
"""

import os
import re
from datetime import datetime
from functools import lru_cache
from typing   import Optional, List

from fastapi              import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic             import BaseModel, Field
from pymongo              import MongoClient
from bson                 import ObjectId
import jwt

# ── Yapılandırma ───────────────────────────────────────────────────────────────
MONGO_URI  = os.environ.get("MONGO_URI", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable must be set.")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable must be set.")
BACKUP_DB  = "facesyma-coach-backup"     # ← sadece buraya yazılır
SOURCE_DB  = "facesyma-backend"          # ← sadece okunur

ALL_LANGS = ["tr","en","de","ru","ar","es","ko","ja",
             "zh","hi","fr","pt","bn","id","ur","it","vi","pl"]

_RE_SIFAT = re.compile(r'^[a-zA-ZçğıöşüÇĞİÖŞÜ0-9 _-]{1,100}$')

COACH_MODULES = [
    "saglik_esenwlik", "dogruluk_sadakat", "guvenlik", "suc_egilim",
    "iliski_yonetimi", "iletisim_becerileri", "stres_yonetimi", "ozguven",
    "zaman_yonetimi", "kisisel_hedefler", "astroloji_harita", "dogum_analizi",
    "yas_koc_ozet", "vucut_dil",
]

EXISTING_MODULES = [
    "kariyer","giyim","liderlik","duygusal","uyum","beceri",
    "ik","tavsiye","motivasyon","astroloji","etkinlik","muzik","film_dizi",
]

_VALID_GOAL_STATUSES = frozenset({'active', 'completed', 'paused', 'failed', 'cancelled'})
_SUPPORTED_LANGUAGES = {
    "tr": {"name": "Türkçe",       "flag": "🇹🇷", "speakers_m": 90},
    "en": {"name": "English",      "flag": "🇬🇧", "speakers_m": 1500},
    "de": {"name": "Deutsch",      "flag": "🇩🇪", "speakers_m": 134},
    "ru": {"name": "Русский",      "flag": "🇷🇺", "speakers_m": 258},
    "ar": {"name": "Arabic",       "flag": "🇸🇦", "speakers_m": 400},
    "es": {"name": "Español",      "flag": "🇪🇸", "speakers_m": 559},
    "ko": {"name": "한국어",        "flag": "🇰🇷", "speakers_m": 82},
    "ja": {"name": "日本語",        "flag": "🇯🇵", "speakers_m": 125},
    "zh": {"name": "中文",          "flag": "🇨🇳", "speakers_m": 1184},
    "hi": {"name": "हिन्दी",        "flag": "🇮🇳", "speakers_m": 609},
    "fr": {"name": "Français",     "flag": "🇫🇷", "speakers_m": 300},
    "pt": {"name": "Português",    "flag": "🇧🇷", "speakers_m": 266},
    "bn": {"name": "বাংলা",        "flag": "🇧🇩", "speakers_m": 284},
    "id": {"name": "Bahasa",       "flag": "🇮🇩", "speakers_m": 252},
    "ur": {"name": "اردو",         "flag": "🇵🇰", "speakers_m": 246},
    "it": {"name": "Italiano",     "flag": "🇮🇹", "speakers_m": 90},
    "vi": {"name": "Tiếng Việt",   "flag": "🇻🇳", "speakers_m": 95},
    "pl": {"name": "Polski",       "flag": "🇵🇱", "speakers_m": 50},
}
_KEY_SCORE     = lambda x: x.get('score', 0)
_PROJ_GOALS    = {"_id": 1, "title": 1, "module": 1, "status": 1, "target_date": 1, "priority": 1}
_COACH_MODULE_DESCRIPTIONS = {
    "saglik_esenwlik":     "Sağlıklı Yaşam ve Esenlik",
    "dogruluk_sadakat":    "Doğruluk ve Sadakat",
    "guvenlik":            "Güvenlik Profili",
    "suc_egilim":          "Risk / Suç Eğilim Analizi",
    "iliski_yonetimi":     "İlişki Yönetimi",
    "iletisim_becerileri": "İletişim Becerileri",
    "stres_yonetimi":      "Stres ve Zaman Yönetimi",
    "ozguven":             "Özgüven Artırma",
    "zaman_yonetimi":      "Zaman Yönetimi",
    "kisisel_hedefler":    "Kişisel Gelişim Hedefleri",
    "astroloji_harita":    "Astroloji Haritası & Yorumları",
    "dogum_analizi":       "Doğum Tarihi/Saati Analizi",
    "yas_koc_ozet":        "Yaşam Koçu Genel Özeti",
    "vucut_dil":           "Beden Dili Analizi",
}

# ── DB bağlantıları ────────────────────────────────────────────────────────────
_mongo_client: Optional[MongoClient] = None

def _get_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client

def get_backup():
    return _get_client()[BACKUP_DB]

def get_source():
    return _get_client()[SOURCE_DB]

# ── JWT ────────────────────────────────────────────────────────────────────────
def get_user_id(authorization: Optional[str] = Header(default=None)) -> Optional[int]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return jwt.decode(
            authorization.split(" ", 1)[1], JWT_SECRET, algorithms=["HS256"]
        ).get("user_id")
    except Exception:
        return None

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Facesyma Yaşam Koçu API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Modeller ──────────────────────────────────────────────────────────────────
class CoachProfileRequest(BaseModel):
    lang:           str            = "tr"
    birth_date:     Optional[str]  = None   # YYYY-MM-DD
    birth_time:     Optional[str]  = None   # HH:MM
    birth_city:     Optional[str]  = None
    birth_timezone: Optional[str]  = "Europe/Istanbul"
    dominant_sifatlar: List[str]   = Field(default_factory=list)

class BirthAnalysisRequest(BaseModel):
    birth_date:     str             # YYYY-MM-DD zorunlu
    birth_time:     Optional[str]  = None
    birth_city:     Optional[str]  = None
    lang:           str            = "tr"

class GoalRequest(BaseModel):
    title:          str
    description:    Optional[str]  = ""
    module:         str            = "kisisel_hedefler"
    target_date:    Optional[str]  = None
    priority:       str            = "orta"   # düşük|orta|yüksek

class AnalyzeRequest(BaseModel):
    analysis_result: dict           # Facesyma analiz çıktısı
    lang:            str = "tr"
    include_modules: List[str] = Field(default_factory=lambda: COACH_MODULES)

class GiyimRequest(BaseModel):
    analysis_result: dict           # /analyze/enhanced/ çıktısı
    lang:            str = "tr"
    mevsim:          Optional[str] = None    # ilkbahar|yaz|sonbahar|kis
    kategori:        Optional[str] = None    # gunluk|spor|resmi|davet
    top_n:           int = 3

# ── Endpoint: Modül listesi ────────────────────────────────────────────────────
@app.get("/coach/modules")
async def list_modules():
    return {
        "existing_modules": EXISTING_MODULES,
        "coach_modules":    COACH_MODULES,
        "total":            len(EXISTING_MODULES) + len(COACH_MODULES),
        "coach_module_descriptions": _COACH_MODULE_DESCRIPTIONS,
    }

# ── Endpoint: Kullanıcı koç profili oluştur/güncelle ─────────────────────────
@app.post("/coach/profile")
async def create_profile(
    body: CoachProfileRequest,
    authorization: Optional[str] = Header(default=None),
):
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")

    db  = get_backup()
    col = db["coach_users"]

    # Astroloji hesapla (doğum tarihi varsa)
    _bd = body.birth_date
    _bbt = body.birth_time
    astro_data = {}
    if _bd:
        astro_data = _calculate_basic_astrology(_bd, _bbt)

    profile = {
        "user_id":          user_id,
        "lang":             body.lang,
        "birth_date":       _bd,
        "birth_time":       _bbt,
        "birth_city":       body.birth_city,
        "birth_timezone":   body.birth_timezone,
        "dominant_sifatlar": body.dominant_sifatlar,
        "updated_at":       (_now_iso := datetime.now().isoformat()),
        **astro_data,
    }

    result = col.update_one(
        {"user_id": user_id},
        {"$set": profile, "$setOnInsert": {"created_at": _now_iso}},
        upsert=True,
    )

    return {"status": "ok", "profile": profile, "astrology": astro_data}


# ── Endpoint: Profil getir ────────────────────────────────────────────────────
@app.get("/coach/profile/{user_id}")
async def get_profile(user_id: int, authorization: Optional[str] = Header(default=None)):
    token_user_id = get_user_id(authorization)
    if not token_user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")
    if token_user_id != user_id:
        raise HTTPException(403, "Bu profile erişim izniniz yok.")
    db  = get_backup()
    doc = db["coach_users"].find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Profil bulunamadı.")
    return doc


# ── Endpoint: Analiz + koç yorumu ────────────────────────────────────────────
@app.post("/coach/analyze")
async def coach_analyze(body: AnalyzeRequest, authorization: Optional[str] = Header(default=None)):
    if not get_user_id(authorization):
        raise HTTPException(401, "Kimlik doğrulama gerekli.")
    """
    Facesyma analiz sonucunu alır, dominant sıfatları belirler,
    backup DB'den her koç modülü için veri getirir ve birleşik
    yaşam koçu yorumu üretir.
    """
    _bl = body.lang
    lang = _bl if _bl in ALL_LANGS else "en"
    db   = get_backup()
    col  = db[f"coach_attributes_{lang}"]

    # Analiz sonucundaki attribute'lardan dominant sıfatları çıkar
    _ar = body.analysis_result
    _arget = _ar.get
    attrs = _arget("attributes", [])
    dominant = [
        a["name"] for a in sorted(attrs, key=_KEY_SCORE, reverse=True)
        if a.get("name")
    ][:5]

    if not dominant:
        raise HTTPException(400, "Analiz sonucunda attribute bulunamadı.")

    # Batch fetch all dominant sıfat docs once (avoids N+1)
    valid_modules = [m for m in body.include_modules if m in COACH_MODULES]
    projection = {"_id": 1, **{m: 1 for m in valid_modules}}
    sifat_docs = {
        doc["_id"]: doc
        for doc in col.find({"_id": {"$in": dominant}}, projection)
    }

    coach_output = {}
    for mod in valid_modules:
        mod_data = [
            {"sifat": sifat, "data": sifat_docs[sifat][mod]}
            for sifat in dominant
            if sifat in sifat_docs and mod in sifat_docs[sifat]
        ]
        if mod_data:
            coach_output[mod] = mod_data

    # Ek analiz verileri
    golden = _arget("golden_ratio", 0)
    face_type = _arget("face_type", "")

    return {
        "dominant_sifatlar": dominant,
        "golden_ratio":      golden,
        "face_type":         face_type,
        "lang":              lang,
        "coach_modules":     coach_output,
        "generated_at":      datetime.now().isoformat(),
    }


# ── Endpoint: Tek sıfat + modül ───────────────────────────────────────────────
@app.get("/coach/sifat/{sifat}/{module}")
async def get_sifat_module(sifat: str, module: str, lang: str = "tr"):
    if not _RE_SIFAT.match(sifat):
        raise HTTPException(400, "Geçersiz sıfat formatı.")
    if module not in COACH_MODULES:
        raise HTTPException(400, f"Geçersiz modül. İzin verilenler: {', '.join(COACH_MODULES)}")
    if lang not in ALL_LANGS:
        lang = "tr"
    db  = get_backup()
    col = db[f"coach_attributes_{lang}"]
    doc = col.find_one({"_id": sifat}, {module: 1, "_id": 0})
    if not doc:
        raise HTTPException(404, f"'{sifat}' sıfatı bulunamadı.")
    if module not in doc:
        raise HTTPException(404, f"'{module}' modülü bu sıfat için mevcut değil.")
    return {"sifat": sifat, "module": module, "data": doc[module], "lang": lang}


# ── Endpoint: Giyim tavsiyesi ─────────────────────────────────────────────────
@app.post("/coach/giyim")
async def coach_giyim(body: GiyimRequest, authorization: Optional[str] = Header(default=None)):
    """
    Analiz sonucundan sıfatları alır, giyim tavsiyesi oluşturur.
    Optional mevsim + kategori filtresi.
    """
    if not get_user_id(authorization):
        raise HTTPException(401, "Kimlik doğrulama gerekli.")
    _bl = body.lang
    lang = _bl if _bl in ALL_LANGS else "tr"
    db = get_backup()
    col = db[f"coach_attributes_{lang}"]

    # Dominant sıfatları çıkar
    _ar = body.analysis_result
    _arget = _ar.get
    attrs = _arget("attributes", [])
    dominant = [
        a["name"] for a in sorted(attrs, key=_KEY_SCORE, reverse=True)
        if a.get("name")
    ][:body.top_n]

    if not dominant:
        raise HTTPException(400, "Analiz sonucunda attribute bulunamadı.")

    # Batch fetch giyim data for all dominant sifats (avoids N+1)
    giyim_base = None
    for doc in col.find({"_id": {"$in": dominant}, "giyim": {"$exists": True}}, {"giyim": 1}):
        if doc.get("giyim"):
            giyim_base = doc["giyim"]
            break

    if not giyim_base:
        # Fallback: karma-adaptif (default) şablonu döndür
        giyim_base = {
            "stil_tipi": "karma-adaptif",
            "coaching": {
                "felsefe": "Uyum ve pragmatizm. Giyim işlevsel, temiz ve herkes tarafından kabul edilebilir.",
                "kombinasyon": "Klasik kombinasyonlar hiçbir zaman başarısız olmaz.",
                "renk_psikolojisi": "Nötr renkler sakinlik ve profesyonellik verir.",
                "yaşam_uyarlamasi": "Hızlı mix-and-match kombinasyonları tercih et."
            },
            "renk_paleti": {"ana": ["#696969", "#808080"], "vurgu": ["#000000"], "kacin": []},
            "yuz_sekli_notu": {
                "oval": "Her kesim uygundur; V-yaka önerilir.",
                "kare": "Yumuşak yuvarlak yaka hatları dengeler.",
                "yuvarlak": "V-yaka ve dikey çizgiler yüzü uzatır.",
                "kalp": "Geniş omuz çizgileri alt yüzü dengeler.",
                "uzun": "Yatay çizgiler ve yüksek yaka dengeler.",
                "elmas": "Geniş yaka ve çan etek alt yapıyı dengeler.",
            },
            "mevsim": {}
        }

    # Mevsim/kategori filtrele
    _mevsim   = body.mevsim
    _kategori = body.kategori
    _gbget = giyim_base.get
    mevsim_onerileri = _gbget("mevsim", {})
    if _mevsim and _mevsim in mevsim_onerileri:
        filtered = {_mevsim: mevsim_onerileri[_mevsim]}
        _fm = filtered[_mevsim]
        if _kategori and _kategori in _fm:
            filtered[_mevsim] = {_kategori: _fm[_kategori]}
        mevsim_onerileri = filtered

    # Cinsiyete göre parça değiştir
    gender = _arget("gender", "").lower()
    if gender == "erkek":
        gender_replacements = _GENDER_REPLACEMENTS

        # Tüm mevsim×kategori parçalarını değiştir
        for mevsim_data in mevsim_onerileri.values():
            for kategori_data in mevsim_data.values():
                if isinstance(kategori_data, dict) and "parca" in kategori_data:
                    # Parça listesini değiştir
                    _kp = kategori_data["parca"]
                    for i, parca in enumerate(_kp):
                        if not isinstance(parca, str):
                            continue
                        for original, replacement in gender_replacements.items():
                            if original.lower() in parca.lower():
                                _kp[i] = parca.replace(original, replacement)
                                break

    # Yüz şekli
    face_type = _arget("face_type", "oval")
    yuz_notu = _gbget("yuz_sekli_notu", {}).get(face_type, "")

    return {
        "dominant_sifatlar": dominant,
        "stil_profili": _gbget("stil_tipi", ""),
        "coaching": _gbget("coaching", {}),
        "yuz_tipi": face_type,
        "lang": lang,
        "renk_paleti": _gbget("renk_paleti", {}),
        "yuz_sekli_notu": yuz_notu,
        "mevsim_onerileri": mevsim_onerileri,
        "generated_at": datetime.now().isoformat(),
    }


# ── Endpoint: Doğum analizi ───────────────────────────────────────────────────
@app.post("/coach/birth")
async def birth_analysis(
    body: BirthAnalysisRequest,
    authorization: Optional[str] = Header(default=None),
):
    user_id  = get_user_id(authorization)
    _bd      = body.birth_date
    _blang   = body.lang
    lang     = _blang if _blang in ALL_LANGS else "en"
    _bbt     = body.birth_time
    astro    = _calculate_basic_astrology(_bd, _bbt, lang)
    numerology = _calculate_numerology(_bd, lang)

    result = {
        "birth_date":  _bd,
        "birth_time":  _bbt,
        "astrology":   astro,
        "numerology":  numerology,
        "lang":        lang,
    }

    # Kullanıcı giriş yapmışsa backup DB'ye kaydet
    if user_id:
        db  = get_backup()
        db["coach_birth_data"].update_one(
            {"user_id": user_id},
            {"$set": {**result, "user_id": user_id,
                      "updated_at": datetime.now().isoformat()}},
            upsert=True,
        )

    return result


# ── Endpoint: Hedefler ────────────────────────────────────────────────────────
@app.get("/coach/goals/{user_id}")
async def get_goals(user_id: int, status: Optional[str] = None, authorization: Optional[str] = Header(default=None)):
    token_user_id = get_user_id(authorization)
    if not token_user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")
    if token_user_id != user_id:
        raise HTTPException(403, "Bu hedeflere erişim izniniz yok.")
    db    = get_backup()
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    goals = list(db["coach_goals"].find(query, _PROJ_GOALS).limit(200))
    for g in goals:
        g["id"] = str(g.pop("_id"))
    return {"goals": goals}


@app.post("/coach/goals")
async def add_goal(
    body: GoalRequest,
    authorization: Optional[str] = Header(default=None),
):
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")

    db     = get_backup()
    result = db["coach_goals"].insert_one({
        "user_id":     user_id,
        "title":       body.title,
        "description": body.description,
        "module":      body.module,
        "target_date": body.target_date,
        "priority":    body.priority,
        "status":      "aktif",
        "created_at":  (_ts := datetime.now().isoformat()),
        "updated_at":  _ts,
    })
    return {"id": str(result.inserted_id), "status": "ok"}


@app.put("/coach/goals/{goal_id}")
async def update_goal(
    goal_id: str,
    status:  str,
    authorization: Optional[str] = Header(default=None),
):
    user_id = get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Kimlik doğrulama gerekli.")

    if status not in _VALID_GOAL_STATUSES:
        raise HTTPException(400, f"Geçersiz status. İzin verilenler: {', '.join(sorted(_VALID_GOAL_STATUSES))}")

    try:
        oid = ObjectId(goal_id)
    except Exception:
        raise HTTPException(400, "Geçersiz goal_id formatı.")

    db = get_backup()
    db["coach_goals"].update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": {"status": status, "updated_at": datetime.now().isoformat()}},
    )
    return {"status": "ok"}


# ── Endpoint: Dil listesi ──────────────────────────────────────────────────────
@app.get("/languages")
async def get_languages():
    return {"languages": _SUPPORTED_LANGUAGES}


# ── Sağlık ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "db": BACKUP_DB, "modules": len(COACH_MODULES)}


# ─────────────────────────────────────────────────────────────────────────────
# Astroloji & Numeroloji yardımcıları
# ─────────────────────────────────────────────────────────────────────────────
_ASTRO_INVALID_DATE = {
    "tr": "Geçersiz tarih formatı — YYYY-MM-DD bekleniyor",
    "en": "Invalid date format — YYYY-MM-DD expected",
    "de": "Ungültiges Datumsformat — YYYY-MM-DD erwartet",
    "ru": "Неверный формат даты — ожидается YYYY-MM-DD",
    "ar": "صيغة التاريخ غير صحيحة — متوقع YYYY-MM-DD",
    "es": "Formato de fecha inválido — se espera YYYY-MM-DD",
    "ko": "유효하지 않은 날짜 형식 — YYYY-MM-DD 필요",
    "ja": "無効な日付形式です — YYYY-MM-DD が必要です",
    "zh": "无效的日期格式 — 预期 YYYY-MM-DD",
    "hi": "अमान्य तारीख प्रारूप — YYYY-MM-DD अपेक्षित",
    "fr": "Format de date invalide — YYYY-MM-DD attendu",
    "pt": "Formato de data inválido — YYYY-MM-DD esperado",
    "bn": "অবৈধ তারিখ বিন্যাস — YYYY-MM-DD প্রত্যাশিত",
    "id": "Format tanggal tidak valid — YYYY-MM-DD diharapkan",
    "ur": "غلط تاریخ کی شکل — YYYY-MM-DD متوقع ہے",
    "it": "Formato di data non valido — YYYY-MM-DD previsto",
    "vi": "Định dạng ngày không hợp lệ — YYYY-MM-DD được mong đợi",
    "pl": "Nieprawidłowy format daty — oczekiwany YYYY-MM-DD",
}
_ASTRO_RISING_HINT = {
    "tr": "Yükselen için tam doğum yeri ve saati gerekli",
    "en": "Rising sign requires full birth location and time",
    "de": "Aszendent benötigt vollständigen Geburtsort und -zeit",
    "ru": "Асцендент требует полного места и времени рождения",
    "ar": "يتطلب برج الطالع موقع الولادة والوقت الكامل",
    "es": "El signo ascendente requiere ubicación y hora completas",
    "ko": "상승점은 완전한 출생지와 시간이 필요합니다",
    "ja": "上昇点には完全な出生地と時刻が必要です",
    "zh": "上升星座需要完整的出生地和时间",
    "hi": "राइजिंग साइन को पूर्ण जन्म स्थान और समय की आवश्यकता है",
    "fr": "Le signe ascendant nécessite le lieu et l'heure complets",
    "pt": "O signo ascendente requer local e hora completos",
    "bn": "উর্ধ্বগামী চিহ্নের জন্য সম্পূর্ণ জন্ম স্থান এবং সময় প্রয়োজন",
    "id": "Tanda rising memerlukan lokasi dan waktu kelahiran lengkap",
    "ur": "صعود ہونے والے نشان کے لیے مکمل پیدائش کی جگہ اور وقت درکار ہے",
    "it": "Il segno ascendente richiede luogo e ora completi",
    "vi": "Dấu hiệu tăng lên yêu cầu địa điểm và giờ sinh hoàn chỉnh",
    "pl": "Znak wschodzący wymaga pełnej lokalizacji i czasu urodzenia",
}
_GENDER_REPLACEMENTS = {
    "elbise": "pantolon",
    "bluz": "gömlek",
    "midi skirt": "chino",
    "crop top": "t-shirt",
    "romper": "overall",
    "wrap dress": "blazer pantolon",
    "maxi dress": "long coat pantolon",
    "turuncu midi dress": "turuncu gömlek",
    "rose midi gown": "rose suit",
    "blush dress": "blush gömlek",
    "pale pink dress": "pale blue gömlek",
    "dusty rose dress": "dusty blue gömlek",
    "burgundy maxi dress": "burgundy suit",
    "blush wool coat": "blush cardigan coat",
}

_ZODIAC_NAMES = {
    "tr": ["Kova","Balık","Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak"],
    "en": ["Aquarius","Pisces","Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn"],
    "de": ["Wassermann","Fische","Widder","Stier","Zwillinge","Krebs","Löwe","Jungfrau","Waage","Skorpion","Schütze","Steinbock"],
    "ru": ["Водолей","Рыбы","Овен","Телец","Близнецы","Рак","Лев","Дева","Весы","Скорпион","Стрелец","Козерог"],
    "ar": ["الدلو","الحوت","الحمل","الثور","الجوزاء","السرطان","الأسد","العذراء","الميزان","العقرب","القوس","الجدي"],
    "es": ["Acuario","Piscis","Aries","Tauro","Géminis","Cáncer","Leo","Virgo","Libra","Escorpio","Sagitario","Capricornio"],
    "ko": ["물병자리","물고기자리","양자리","황소자리","쌍둥이자리","게자리","사자자리","처녀자리","천칭자리","전갈자리","궁수자리","염소자리"],
    "ja": ["水瓶座","魚座","牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座","天秤座","蠍座","射手座","山羊座"],
    "zh": ["水瓶座","双鱼座","白羊座","金牛座","双子座","巨蟹座","狮子座","处女座","天秤座","天蝎座","射手座","摩羯座"],
    "hi": ["कुंभ","मीन","मेष","वृष","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर"],
    "fr": ["Verseau","Poissons","Bélier","Taureau","Gémeaux","Cancer","Lion","Vierge","Balance","Scorpion","Sagittaire","Capricorne"],
    "pt": ["Aquário","Peixes","Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio"],
    "bn": ["কুম্ভ","মীন","মেষ","বৃষ","মিথুন","কর্কট","সিংহ","কন্যা","তুলা","বৃশ্চিক","ধনু","মকর"],
    "id": ["Aquarius","Pisces","Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagitarius","Capricorn"],
    "ur": ["دلو","مچھلی","مेश","ثور","جوزا","سرطان","اسد","کنیا","میزان","عقرب","قوس","جدی"],
    "it": ["Acquario","Pesci","Ariete","Toro","Gemelli","Cancro","Leone","Vergine","Bilancia","Scorpione","Sagittario","Capricorno"],
    "vi": ["Bảo Bình","Song Ngư","Bạch Dương","Kim Ngưu","Thị Nhan","巨蟹","Sư Tử","Xử Nữ","Thiên Bình","Bọ Cạp","Nhân Mã","Ma Kết"],
    "pl": ["Wodnik","Ryby","Baran","Byk","Bliźnięta","Rak","Lew","Panna","Waga","Skorpion","Strzelec","Kozioł"],
}

_ELEMENTS = {
    "tr": {0:"Hava", 1:"Su", 2:"Ateş", 3:"Toprak", 4:"Hava", 5:"Su", 6:"Ateş", 7:"Toprak", 8:"Hava", 9:"Su", 10:"Ateş", 11:"Toprak"},
    "en": {0:"Air", 1:"Water", 2:"Fire", 3:"Earth", 4:"Air", 5:"Water", 6:"Fire", 7:"Earth", 8:"Air", 9:"Water", 10:"Fire", 11:"Earth"},
    "de": {0:"Luft", 1:"Wasser", 2:"Feuer", 3:"Erde", 4:"Luft", 5:"Wasser", 6:"Feuer", 7:"Erde", 8:"Luft", 9:"Wasser", 10:"Feuer", 11:"Erde"},
    "ru": {0:"Воздух", 1:"Вода", 2:"Огонь", 3:"Земля", 4:"Воздух", 5:"Вода", 6:"Огонь", 7:"Земля", 8:"Воздух", 9:"Вода", 10:"Огонь", 11:"Земля"},
    "ar": {0:"هواء", 1:"ماء", 2:"نار", 3:"تراب", 4:"هواء", 5:"ماء", 6:"نار", 7:"تراب", 8:"هواء", 9:"ماء", 10:"نار", 11:"تراب"},
    "es": {0:"Aire", 1:"Agua", 2:"Fuego", 3:"Tierra", 4:"Aire", 5:"Agua", 6:"Fuego", 7:"Tierra", 8:"Aire", 9:"Agua", 10:"Fuego", 11:"Tierra"},
    "ko": {0:"공기", 1:"물", 2:"불", 3:"흙", 4:"공기", 5:"물", 6:"불", 7:"흙", 8:"공기", 9:"물", 10:"불", 11:"흙"},
    "ja": {0:"風", 1:"水", 2:"火", 3:"土", 4:"風", 5:"水", 6:"火", 7:"土", 8:"風", 9:"水", 10:"火", 11:"土"},
    "zh": {0:"风", 1:"水", 2:"火", 3:"土", 4:"风", 5:"水", 6:"火", 7:"土", 8:"风", 9:"水", 10:"火", 11:"土"},
    "hi": {0:"वायु", 1:"जल", 2:"अग्नि", 3:"पृथ्वी", 4:"वायु", 5:"जल", 6:"अग्नि", 7:"पृथ्वी", 8:"वायु", 9:"जल", 10:"अग्नि", 11:"पृथ्वी"},
    "fr": {0:"Air", 1:"Eau", 2:"Feu", 3:"Terre", 4:"Air", 5:"Eau", 6:"Feu", 7:"Terre", 8:"Air", 9:"Eau", 10:"Feu", 11:"Terre"},
    "pt": {0:"Ar", 1:"Água", 2:"Fogo", 3:"Terra", 4:"Ar", 5:"Água", 6:"Fogo", 7:"Terra", 8:"Ar", 9:"Água", 10:"Fogo", 11:"Terra"},
    "bn": {0:"বায়ু", 1:"জল", 2:"আগুন", 3:"মাটি", 4:"বায়ু", 5:"জল", 6:"আগুন", 7:"মাটি", 8:"বায়ু", 9:"জল", 10:"আগুন", 11:"মাটি"},
    "id": {0:"Udara", 1:"Air", 2:"Api", 3:"Tanah", 4:"Udara", 5:"Air", 6:"Api", 7:"Tanah", 8:"Udara", 9:"Air", 10:"Api", 11:"Tanah"},
    "ur": {0:"ہوا", 1:"پانی", 2:"آگ", 3:"مٹی", 4:"ہوا", 5:"پانی", 6:"آگ", 7:"مٹی", 8:"ہوا", 9:"پانی", 10:"آگ", 11:"مٹی"},
    "it": {0:"Aria", 1:"Acqua", 2:"Fuoco", 3:"Terra", 4:"Aria", 5:"Acqua", 6:"Fuoco", 7:"Terra", 8:"Aria", 9:"Acqua", 10:"Fuoco", 11:"Terra"},
    "vi": {0:"Không khí", 1:"Nước", 2:"Lửa", 3:"Đất", 4:"Không khí", 5:"Nước", 6:"Lửa", 7:"Đất", 8:"Không khí", 9:"Nước", 10:"Lửa", 11:"Đất"},
    "pl": {0:"Powietrze", 1:"Woda", 2:"Ogień", 3:"Ziemia", 4:"Powietrze", 5:"Woda", 6:"Ogień", 7:"Ziemia", 8:"Powietrze", 9:"Woda", 10:"Ogień", 11:"Ziemia"},
}

_QUALITIES = {
    "tr": {0:"Kardinal", 1:"Su", 2:"Kardinal", 3:"Sabit", 4:"Değişken", 5:"Kardinal", 6:"Sabit", 7:"Değişken", 8:"Kardinal", 9:"Sabit", 10:"Değişken", 11:"Kardinal"},
    "en": {0:"Cardinal", 1:"Water", 2:"Cardinal", 3:"Fixed", 4:"Mutable", 5:"Cardinal", 6:"Fixed", 7:"Mutable", 8:"Cardinal", 9:"Fixed", 10:"Mutable", 11:"Cardinal"},
    "de": {0:"Kardinal", 1:"Wasser", 2:"Kardinal", 3:"Fest", 4:"Veränderlich", 5:"Kardinal", 6:"Fest", 7:"Veränderlich", 8:"Kardinal", 9:"Fest", 10:"Veränderlich", 11:"Kardinal"},
    "ru": {0:"Кардинальный", 1:"Вода", 2:"Кардинальный", 3:"Фиксированный", 4:"Мутабельный", 5:"Кардинальный", 6:"Фиксированный", 7:"Мутабельный", 8:"Кардинальный", 9:"Фиксированный", 10:"Мутабельный", 11:"Кардинальный"},
    "ar": {0:"أساسي", 1:"ماء", 2:"أساسي", 3:"ثابت", 4:"متغير", 5:"أساسي", 6:"ثابت", 7:"متغير", 8:"أساسي", 9:"ثابت", 10:"متغير", 11:"أساسي"},
    "es": {0:"Cardinal", 1:"Agua", 2:"Cardinal", 3:"Fijo", 4:"Mutable", 5:"Cardinal", 6:"Fijo", 7:"Mutable", 8:"Cardinal", 9:"Fijo", 10:"Mutable", 11:"Cardinal"},
    "ko": {0:"기본", 1:"물", 2:"기본", 3:"고정", 4:"유동", 5:"기본", 6:"고정", 7:"유동", 8:"기본", 9:"고정", 10:"유동", 11:"기본"},
    "ja": {0:"活動", 1:"水", 2:"活動", 3:"不動", 4:"柔軟", 5:"活動", 6:"不動", 7:"柔軟", 8:"活動", 9:"不動", 10:"柔軟", 11:"活動"},
    "zh": {0:"基本", 1:"水", 2:"基本", 3:"固定", 4:"变动", 5:"基本", 6:"固定", 7:"变动", 8:"基本", 9:"固定", 10:"变动", 11:"基本"},
    "hi": {0:"मुख्य", 1:"जल", 2:"मुख्य", 3:"निश्चित", 4:"परिवर्तनशील", 5:"मुख्य", 6:"निश्चित", 7:"परिवर्तनशील", 8:"मुख्य", 9:"निश्चित", 10:"परिवर्तनशील", 11:"मुख्य"},
    "fr": {0:"Cardinal", 1:"Eau", 2:"Cardinal", 3:"Fixe", 4:"Mutable", 5:"Cardinal", 6:"Fixe", 7:"Mutable", 8:"Cardinal", 9:"Fixe", 10:"Mutable", 11:"Cardinal"},
    "pt": {0:"Cardinal", 1:"Água", 2:"Cardinal", 3:"Fixo", 4:"Mutável", 5:"Cardinal", 6:"Fixo", 7:"Mutável", 8:"Cardinal", 9:"Fixo", 10:"Mutável", 11:"Cardinal"},
    "bn": {0:"মূল", 1:"জল", 2:"মূল", 3:"স্থিতিশীল", 4:"পরিবর্তনশীল", 5:"মূল", 6:"স্থিতিশীল", 7:"পরিবর্তনশীল", 8:"মূল", 9:"স্থিতিশীল", 10:"পরিবর্তনশীল", 11:"মূল"},
    "id": {0:"Kardinal", 1:"Air", 2:"Kardinal", 3:"Tetap", 4:"Berubah", 5:"Kardinal", 6:"Tetap", 7:"Berubah", 8:"Kardinal", 9:"Tetap", 10:"Berubah", 11:"Kardinal"},
    "ur": {0:"بنیادی", 1:"پانی", 2:"بنیادی", 3:"مقرر", 4:"متغیر", 5:"بنیادی", 6:"مقرر", 7:"متغیر", 8:"بنیادی", 9:"مقرر", 10:"متغیر", 11:"بنیادی"},
    "it": {0:"Cardinale", 1:"Acqua", 2:"Cardinale", 3:"Fisso", 4:"Mobile", 5:"Cardinale", 6:"Fisso", 7:"Mobile", 8:"Cardinale", 9:"Fisso", 10:"Mobile", 11:"Cardinale"},
    "vi": {0:"Chính", 1:"Nước", 2:"Chính", 3:"Cố định", 4:"Linh hoạt", 5:"Chính", 6:"Cố định", 7:"Linh hoạt", 8:"Chính", 9:"Cố định", 10:"Linh hoạt", 11:"Chính"},
    "pl": {0:"Kardynalny", 1:"Woda", 2:"Kardynalny", 3:"Stały", 4:"Zmienny", 5:"Kardynalny", 6:"Stały", 7:"Zmienny", 8:"Kardynalny", 9:"Stały", 10:"Zmienny", 11:"Kardynalny"},
}

_SEASONS = {
    "tr": {1:"Kış", 2:"Kış", 3:"İlkbahar", 4:"İlkbahar", 5:"İlkbahar", 6:"Yaz", 7:"Yaz", 8:"Yaz", 9:"Sonbahar", 10:"Sonbahar", 11:"Sonbahar", 12:"Kış"},
    "en": {1:"Winter", 2:"Winter", 3:"Spring", 4:"Spring", 5:"Spring", 6:"Summer", 7:"Summer", 8:"Summer", 9:"Autumn", 10:"Autumn", 11:"Autumn", 12:"Winter"},
    "de": {1:"Winter", 2:"Winter", 3:"Frühling", 4:"Frühling", 5:"Frühling", 6:"Sommer", 7:"Sommer", 8:"Sommer", 9:"Herbst", 10:"Herbst", 11:"Herbst", 12:"Winter"},
    "ru": {1:"Зима", 2:"Зима", 3:"Весна", 4:"Весна", 5:"Весна", 6:"Лето", 7:"Лето", 8:"Лето", 9:"Осень", 10:"Осень", 11:"Осень", 12:"Зима"},
    "ar": {1:"شتاء", 2:"شتاء", 3:"ربيع", 4:"ربيع", 5:"ربيع", 6:"صيف", 7:"صيف", 8:"صيف", 9:"خريف", 10:"خريف", 11:"خريف", 12:"شتاء"},
    "es": {1:"Invierno", 2:"Invierno", 3:"Primavera", 4:"Primavera", 5:"Primavera", 6:"Verano", 7:"Verano", 8:"Verano", 9:"Otoño", 10:"Otoño", 11:"Otoño", 12:"Invierno"},
    "ko": {1:"겨울", 2:"겨울", 3:"봄", 4:"봄", 5:"봄", 6:"여름", 7:"여름", 8:"여름", 9:"가을", 10:"가을", 11:"가을", 12:"겨울"},
    "ja": {1:"冬", 2:"冬", 3:"春", 4:"春", 5:"春", 6:"夏", 7:"夏", 8:"夏", 9:"秋", 10:"秋", 11:"秋", 12:"冬"},
    "zh": {1:"冬季", 2:"冬季", 3:"春季", 4:"春季", 5:"春季", 6:"夏季", 7:"夏季", 8:"夏季", 9:"秋季", 10:"秋季", 11:"秋季", 12:"冬季"},
    "hi": {1:"सर्दी", 2:"सर्दी", 3:"वसंत", 4:"वसंत", 5:"वसंत", 6:"गर्मी", 7:"गर्मी", 8:"गर्मी", 9:"पतझड़", 10:"पतझड़", 11:"पतझड़", 12:"सर्दी"},
    "fr": {1:"Hiver", 2:"Hiver", 3:"Printemps", 4:"Printemps", 5:"Printemps", 6:"Été", 7:"Été", 8:"Été", 9:"Automne", 10:"Automne", 11:"Automne", 12:"Hiver"},
    "pt": {1:"Inverno", 2:"Inverno", 3:"Primavera", 4:"Primavera", 5:"Primavera", 6:"Verão", 7:"Verão", 8:"Verão", 9:"Outono", 10:"Outono", 11:"Outono", 12:"Inverno"},
    "bn": {1:"শীত", 2:"শীত", 3:"বসন্ত", 4:"বসন্ত", 5:"বসন্ত", 6:"গ্রীষ্ম", 7:"গ্রীষ্ম", 8:"গ্রীষ্ম", 9:"শরৎ", 10:"শরৎ", 11:"শরৎ", 12:"শীত"},
    "id": {1:"Musim Dingin", 2:"Musim Dingin", 3:"Musim Semi", 4:"Musim Semi", 5:"Musim Semi", 6:"Musim Panas", 7:"Musim Panas", 8:"Musim Panas", 9:"Musim Gugur", 10:"Musim Gugur", 11:"Musim Gugur", 12:"Musim Dingin"},
    "ur": {1:"سردی", 2:"سردی", 3:"بہار", 4:"بہار", 5:"بہار", 6:"گرمی", 7:"گرمی", 8:"گرمی", 9:"خزاں", 10:"خزاں", 11:"خزاں", 12:"سردی"},
    "it": {1:"Inverno", 2:"Inverno", 3:"Primavera", 4:"Primavera", 5:"Primavera", 6:"Estate", 7:"Estate", 8:"Estate", 9:"Autunno", 10:"Autunno", 11:"Autunno", 12:"Inverno"},
    "vi": {1:"Mùa Đông", 2:"Mùa Đông", 3:"Mùa Xuân", 4:"Mùa Xuân", 5:"Mùa Xuân", 6:"Mùa Hè", 7:"Mùa Hè", 8:"Mùa Hè", 9:"Mùa Thu", 10:"Mùa Thu", 11:"Mùa Thu", 12:"Mùa Đông"},
    "pl": {1:"Zima", 2:"Zima", 3:"Wiosna", 4:"Wiosna", 5:"Wiosna", 6:"Lato", 7:"Lato", 8:"Lato", 9:"Jesień", 10:"Jesień", 11:"Jesień", 12:"Zima"},
}

_TIME_ENERGIES = {
    "tr": {(1,6): "Sezgisel ve manevi", (7,11): "Yaratıcı ve başlangıç", (12,17): "Sosyal ve işbirlikçi", (18,23): "Analitik ve planlayıcı", (0,0): "Dönüşümsel"},
    "en": {(1,6): "Intuitive and spiritual", (7,11): "Creative and initiating", (12,17): "Social and collaborative", (18,23): "Analytical and planning", (0,0): "Transformative"},
    "de": {(1,6): "Intuitiv und spirituell", (7,11): "Kreativ und initiativ", (12,17): "Sozial und kooperativ", (18,23): "Analytisch und planend", (0,0): "Transformativ"},
    "ru": {(1,6): "Интуитивный и духовный", (7,11): "Творческий и инициативный", (12,17): "Социальный и совместный", (18,23): "Аналитический и плановый", (0,0): "Трансформативный"},
    "ar": {(1,6): "بديهي وروحاني", (7,11): "إبداعي وريادي", (12,17): "اجتماعي وتعاوني", (18,23): "تحليلي وتخطيطي", (0,0): "تحويلي"},
    "es": {(1,6): "Intuitivo y espiritual", (7,11): "Creativo e iniciador", (12,17): "Social y colaborativo", (18,23): "Analítico y planificador", (0,0): "Transformador"},
    "ko": {(1,6): "직관적이고 영적", (7,11): "창의적이고 개척적", (12,17): "사회적이고 협력적", (18,23): "분석적이고 계획적", (0,0): "변혁적"},
    "ja": {(1,6): "直感的でスピリチュアル", (7,11): "創造的でイニシアティブ", (12,17): "社会的で協力的", (18,23): "分析的で計画的", (0,0): "変革的"},
    "zh": {(1,6): "直观和精神", (7,11): "创意和开创", (12,17): "社交和协作", (18,23): "分析和计划", (0,0): "变革"},
    "hi": {(1,6): "सहज और आध्यात्मिक", (7,11): "रचनात्मक और पहलकदमी", (12,17): "सामाजिक और सहयोगी", (18,23): "विश्लेषणात्मक और योजनाकार", (0,0): "रूपांतरकारी"},
    "fr": {(1,6): "Intuitif et spirituel", (7,11): "Créatif et initiateur", (12,17): "Social et collaboratif", (18,23): "Analytique et planificateur", (0,0): "Transformatif"},
    "pt": {(1,6): "Intuitivo e espiritual", (7,11): "Criativo e iniciador", (12,17): "Social e colaborativo", (18,23): "Analítico e planejador", (0,0): "Transformador"},
    "bn": {(1,6): "স্বজ্ঞাত এবং আধ্যাত্মিক", (7,11): "সৃজনশীল এবং উদ্যোক্তা", (12,17): "সামাজিক এবং সহযোগী", (18,23): "বিশ্লেষণাত্মক এবং পরিকল্পনাকারী", (0,0): "রূপান্তরকারী"},
    "id": {(1,6): "Intuitif dan spiritual", (7,11): "Kreatif dan inisiatif", (12,17): "Sosial dan kolaboratif", (18,23): "Analitik dan perencanaan", (0,0): "Transformatif"},
    "ur": {(1,6): "شہادت اور روحانی", (7,11): "تخلیقی اور ابتدائی", (12,17): "سماجی اور تعاونی", (18,23): "تجزیاتی اور منصوبہ بندی", (0,0): "تبدیلی کا"},
    "it": {(1,6): "Intuitivo e spirituale", (7,11): "Creativo e iniziatore", (12,17): "Sociale e collaborativo", (18,23): "Analitico e pianificatore", (0,0): "Trasformativo"},
    "vi": {(1,6): "Trực giác và tâm linh", (7,11): "Sáng tạo và sáng kiến", (12,17): "Xã hội và hợp tác", (18,23): "Phân tích và lập kế hoạch", (0,0): "Biến đổi"},
    "pl": {(1,6): "Intuicyjny i duchowy", (7,11): "Kreatywny i inicjujący", (12,17): "Społeczny i współpracujący", (18,23): "Analityczny i planujący", (0,0): "Transformacyjny"},
}

_NUMEROLOGY_MEANINGS = {
    "tr": {1:"Lider, öncü, bağımsız", 2:"Diplomat, uyumlu, destekleyici", 3:"Yaratıcı, ifadeci, sosyal", 4:"Pratik, güvenilir, disiplinli", 5:"Özgürlükçü, maceracı, uyumlu", 6:"Bakıcı, sorumluluk sahibi, uyumlu", 7:"Analist, mistik, içe dönük", 8:"Güç, maddi başarı, otorite", 9:"İnsancıl, idealist, yaratıcı", 11:"Sezgisel usta", 22:"Mimar usta", 33:"Şifacı usta"},
    "en": {1:"Leader, pioneer, independent", 2:"Diplomat, harmonious, supportive", 3:"Creative, expressive, social", 4:"Practical, reliable, disciplined", 5:"Freedom-loving, adventurous, adaptable", 6:"Caretaker, responsible, harmonious", 7:"Analyst, mystic, introspective", 8:"Power, material success, authority", 9:"Humanitarian, idealistic, creative", 11:"Intuitive master", 22:"Architect master", 33:"Healer master"},
    "de": {1:"Anführer, Pionier, unabhängig", 2:"Diplomat, harmonisch, unterstützend", 3:"Kreativ, ausdrucksstark, sozial", 4:"Praktisch, zuverlässig, diszipliniert", 5:"Freiheitsliebend, abenteuerlustig, anpassungsfähig", 6:"Pfleger, verantwortungsvoll, harmonisch", 7:"Analytiker, mystisch, introvertiert", 8:"Macht, materieller Erfolg, Autorität", 9:"Humanitär, idealistisch, kreativ", 11:"Intuitiver Meister", 22:"Architektur-Meister", 33:"Heiler-Meister"},
    "ru": {1:"Лидер, первопроходец, независимый", 2:"Дипломат, гармоничный, поддерживающий", 3:"Творческий, выразительный, социальный", 4:"Практичный, надежный, дисциплинированный", 5:"Свободолюбивый, авантюрный, адаптивный", 6:"Опекун, ответственный, гармоничный", 7:"Аналитик, мистический, интровертный", 8:"Власть, материальный успех, авторитет", 9:"Гуманитарный, идеалистический, творческий", 11:"Интуитивный мастер", 22:"Архитектор-мастер", 33:"Целитель-мастер"},
    "ar": {1:"قائد، رائد، مستقل", 2:"دبلوماسي، متناغم، داعم", 3:"مبدع، تعبيري، اجتماعي", 4:"عملي، موثوق، منضبط", 5:"محب للحرية، مغامر، متكيف", 6:"مقدم رعاية، مسؤول، متناغم", 7:"محلل، غامض، منطوٍ", 8:"القوة، النجاح المادي، السلطة", 9:"إنساني، مثالي، مبدع", 11:"معلم حدسي", 22:"معلم معماري", 33:"معلم شاف"},
    "es": {1:"Líder, pionero, independiente", 2:"Diplomático, armónico, de apoyo", 3:"Creativo, expresivo, social", 4:"Práctico, confiable, disciplinado", 5:"Amante de la libertad, aventurero, adaptable", 6:"Cuidador, responsable, armónico", 7:"Analista, místico, introvertido", 8:"Poder, éxito material, autoridad", 9:"Humanitario, idealista, creativo", 11:"Maestro intuitivo", 22:"Maestro arquitecto", 33:"Maestro sanador"},
    "ko": {1:"지도자, 개척자, 독립적", 2:"외교관, 조화로운, 지지적", 3:"창의적, 표현적, 사회적", 4:"실용적, 신뢰할 수 있는, 규율 있는", 5:"자유를 사랑하는, 모험적, 적응 가능", 6:"간병인, 책임 있는, 조화로운", 7:"분석가, 신비로운, 내향적", 8:"권력, 물질적 성공, 권위", 9:"인도주의적, 이상주의적, 창의적", 11:"직관적 마스터", 22:"건축 마스터", 33:"치유 마스터"},
    "ja": {1:"指導者、開拓者、独立的", 2:"外交官、調和的、支援的", 3:"創意的、表現的、社交的", 4:"実用的、信頼できる、規律的", 5:"自由を愛する、冒険心豊か、適応可能", 6:"介護者、責任のある、調和的", 7:"分析家、神秘的、内向的", 8:"力、物質的成功、権威", 9:"人道的、理想主義的、創意的", 11:"直感的マスター", 22:"建築マスター", 33:"ヒーラーマスター"},
    "zh": {1:"领导者、先驱、独立", 2:"外交官、和谐、支持", 3:"创意、表达、社交", 4:"实用、可靠、纪律", 5:"爱自由、冒险、适应", 6:"照顾者、负责、和谐", 7:"分析家、神秘、内向", 8:"力量、物质成功、权威", 9:"人道、理想、创意", 11:"直觉大师", 22:"建筑大师", 33:"治疗大师"},
    "hi": {1:"नेता, अग्रदूत, स्वतंत्र", 2:"कूटनीतिज्ञ, सामंजस्यपूर्ण, सहायक", 3:"रचनात्मक, अभिव्यक्तिपूर्ण, सामाजिक", 4:"व्यावहारिक, विश्वसनीय, अनुशासित", 5:"स्वतंत्रता प्रेमी, साहसी, अनुकूलनीय", 6:"देखभालकर्ता, जिम्मेदार, सामंजस्यपूर्ण", 7:"विश्लेषक, रहस्यमय, अंतर्मुखी", 8:"शक्ति, भौतिक सफलता, अधिकार", 9:"मानवतावादी, आदर्शवादी, रचनात्मक", 11:"अंतर्ज्ञानी मास्टर", 22:"आर्किटेक्ट मास्टर", 33:"हीलर मास्टर"},
    "fr": {1:"Leader, pionnier, indépendant", 2:"Diplomate, harmonieux, solidaire", 3:"Créatif, expressif, social", 4:"Pratique, fiable, discipliné", 5:"Libertaire, aventurier, adaptable", 6:"Soignant, responsable, harmonieux", 7:"Analyste, mystique, introverti", 8:"Pouvoir, succès matériel, autorité", 9:"Humanitaire, idéaliste, créatif", 11:"Maître intuitif", 22:"Maître architecte", 33:"Maître guérisseur"},
    "pt": {1:"Líder, pioneiro, independente", 2:"Diplomata, harmônico, solidário", 3:"Criativo, expressivo, social", 4:"Prático, confiável, disciplinado", 5:"Amante da liberdade, aventureiro, adaptável", 6:"Cuidador, responsável, harmônico", 7:"Analista, místico, introvertido", 8:"Poder, sucesso material, autoridade", 9:"Humanitário, idealista, criativo", 11:"Mestre intuitivo", 22:"Mestre arquiteto", 33:"Mestre curador"},
    "bn": {1:"নেতা, অগ্রগামী, স্বাধীন", 2:"কূটনীতিজ্ঞ, সামঞ্জস্যপূর্ণ, সহায়ক", 3:"সৃজনশীল, প্রকাশমূলক, সামাজিক", 4:"ব্যবহারিক, নির্ভরযোগ্য, শৃঙ্খলাবদ্ধ", 5:"স্বাধীনতা প্রেমী, দুঃসাহসী, অভিযোজিত", 6:"যত্নশীল, দায়বদ্ধ, সামঞ্জস্যপূর্ণ", 7:"বিশ্লেষক, রহস্যময়, অন্তর্মুখী", 8:"শক্তি, বস্তুগত সাফল্য, কর্তৃপক্ষ", 9:"মানবিক, আদর্শবাদী, সৃজনশীল", 11:"স্বজ্ঞাত মাস্টার", 22:"স্থপতি মাস্টার", 33:"নিরাময়কারী মাস্টার"},
    "id": {1:"Pemimpin, pelopor, independen", 2:"Diplomat, harmonis, suportif", 3:"Kreatif, ekspresif, sosial", 4:"Praktis, dapat diandalkan, disiplin", 5:"Pecinta kebebasan, petualang, adaptif", 6:"Penasehat, bertanggung jawab, harmonis", 7:"Analis, mistis, introvert", 8:"Kekuatan, kesuksesan material, otoritas", 9:"Humaniter, idealis, kreatif", 11:"Ahli intuitif", 22:"Ahli arsitektur", 33:"Ahli penyembuh"},
    "ur": {1:"رہنما، علمبردار، خود مختار", 2:"سفارتکار، ہماہنگ، معاون", 3:"تخلیقی، اظہاری، سماجی", 4:"عملی، قابل اعتماد، نظم و ضبط", 5:"آزادی سے محبت، مہم جو، موافق", 6:"دیکھ بھال کار، ذمہ دار، ہماہنگ", 7:"تجزیہ کار، غامض، باطن پسند", 8:"طاقت، مادی کامیابی، اقتدار", 9:"انسان دوست، نظریہ پرست، تخلیقی", 11:"شہادت رکھنے والا ماہر", 22:"معماری ماہر", 33:"شفاء دینے والا ماہر"},
    "it": {1:"Leader, pioniere, indipendente", 2:"Diplomatico, armonico, solidale", 3:"Creativo, espressivo, sociale", 4:"Pratico, affidabile, disciplinato", 5:"Amante della libertà, avventuriero, adattabile", 6:"Caregiver, responsabile, armonico", 7:"Analista, mistico, introverso", 8:"Potere, successo materiale, autorità", 9:"Umanitario, idealista, creativo", 11:"Maestro intuitivo", 22:"Maestro architetto", 33:"Maestro guaritore"},
    "vi": {1:"Lãnh đạo, tiên phong, độc lập", 2:"Ngoại giao, hài hòa, hỗ trợ", 3:"Sáng tạo, biểu hiện, xã hội", 4:"Thực tế, đáng tin cậy, kỷ luật", 5:"Yêu thích tự do, mạo hiểm, thích ứng", 6:"Chăm sóc, có trách nhiệm, hài hòa", 7:"Nhà phân tích, bí ẩn, hướng nội", 8:"Sức mạnh, thành công vật chất, quyền hạn", 9:"Nhân đạo, lý tưởng, sáng tạo", 11:"Bậc thầy trực giác", 22:"Bậc thầy kiến trúc", 33:"Bậc thầy chữa bệnh"},
    "pl": {1:"Lider, pionier, niezależny", 2:"Dyplomata, harmonijny, wspierający", 3:"Kreatywny, ekspresyjny, społeczny", 4:"Praktyczny, niezawodny, zdyscyplinowany", 5:"Miłośnik wolności, awanturnik, adaptacyjny", 6:"Opiekun, odpowiedzialny, harmonijny", 7:"Analityk, mistyczny, introwertyzm", 8:"Moc, sukcesy materialne, autorytet", 9:"Humanitarny, idealistyczny, kreatywny", 11:"Mistrz intuicji", 22:"Mistrz architektury", 33:"Mistrz uzdrawiania"},
}

def _calculate_basic_astrology(birth_date_str: str, birth_time_str: Optional[str] = None, lang: str = "tr") -> dict:
    """
    Basic astrology calculation — zodiac, element, quality from birth date.
    Supports 18 languages.
    """
    _dsp = datetime.strptime
    try:
        bd = _dsp(birth_date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": _ASTRO_INVALID_DATE.get(lang, _ASTRO_INVALID_DATE["en"])}

    _bdm = bd.month
    _bdd = bd.day
    sun_sign = _get_sun_sign(_bdm, _bdd, lang)
    element  = _get_element(sun_sign, lang)
    quality  = _get_quality(sun_sign, lang)

    result = {
        "sun_sign":      sun_sign,
        "element":       element,
        "quality":       quality,
        "birth_month":   _bdm,
        "birth_day":     _bdd,
        "birth_year":    bd.year,
        "season":        _get_season(_bdm, lang),
        "day_of_week":   bd.strftime("%A"),
    }

    if birth_time_str:
        try:
            bt = _dsp(birth_time_str, "%H:%M")
            _bth = bt.hour
            result["birth_hour"]     = _bth
            result["time_energy"]    = _get_time_energy(_bth, lang)
            result["rising_hint"]    = _ASTRO_RISING_HINT.get(lang, _ASTRO_RISING_HINT["en"])
        except ValueError:
            pass

    return result


@lru_cache(maxsize=256)
def _get_sun_sign(month: int, day: int, lang: str = "tr") -> str:
    """Get zodiac sign in specified language — supports 18 languages"""
    signs_dates = [
        ((1,20),(2,18),0),   ((2,19),(3,20),1),   ((3,21),(4,19),2),   ((4,20),(5,20),3),
        ((5,21),(6,20),4),   ((6,21),(7,22),5),   ((7,23),(8,22),6),   ((8,23),(9,22),7),
        ((9,23),(10,22),8),  ((10,23),(11,21),9), ((11,22),(12,21),10),((12,22),(1,19),11),
    ]

    _znget = _ZODIAC_NAMES.get
    _znen  = _ZODIAC_NAMES["en"]
    for (sm,sd),(em,ed),idx in signs_dates:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            names = _znget(lang, _znen)
            return names[idx]

    names = _znget(lang, _znen)
    return names[11]  # Default to Capricorn/last sign


@lru_cache(maxsize=64)
def _get_element(sign_idx: int, lang: str = "tr") -> str:
    """Get element (fire, earth, air, water) in specified language"""
    elem_dict = _ELEMENTS.get(lang, _ELEMENTS["en"])
    return elem_dict.get(sign_idx, "Unknown")


@lru_cache(maxsize=64)
def _get_quality(sign_idx: int, lang: str = "tr") -> str:
    """Get quality (cardinal, fixed, mutable) in specified language"""
    qual_dict = _QUALITIES.get(lang, _QUALITIES["en"])
    return qual_dict.get(sign_idx, "Unknown")


@lru_cache(maxsize=64)
def _get_season(month: int, lang: str = "tr") -> str:
    """Get season name in specified language"""
    season_dict = _SEASONS.get(lang, _SEASONS["en"])
    return season_dict.get(month, "Unknown")


@lru_cache(maxsize=64)
def _get_time_energy(hour: int, lang: str = "tr") -> str:
    """Get time energy description in specified language"""
    energy_dict = _TIME_ENERGIES.get(lang, _TIME_ENERGIES["en"])
    if 1 <= hour <= 6:
        return energy_dict[(1,6)]
    elif 7 <= hour <= 11:
        return energy_dict[(7,11)]
    elif 12 <= hour <= 17:
        return energy_dict[(12,17)]
    elif 18 <= hour <= 23:
        return energy_dict[(18,23)]
    else:
        return energy_dict[(0,0)]


def _calculate_numerology(birth_date_str: str, lang: str = "tr") -> dict:
    """Basic numerology calculation — supports 18 languages"""
    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d")
    except ValueError:
        return {}

    def reduce(n: int) -> int:
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    day   = reduce(bd.day)
    month = reduce(bd.month)
    year  = reduce(sum(int(d) for d in str(bd.year)))
    life  = reduce(day + month + year)

    meaning_dict = _NUMEROLOGY_MEANINGS.get(lang, _NUMEROLOGY_MEANINGS["en"])

    return {
        "life_path_number": life,
        "life_path_meaning": meaning_dict.get(life, ""),
        "day_number":   day,
        "month_number": month,
        "year_number":  year,
    }
