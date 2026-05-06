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
import logging
from datetime import datetime
from functools import lru_cache
from typing   import Optional, List

try:
    from kerykeion import AstrologicalSubject
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder
    _KERYKEION_OK = True
    _TF = TimezoneFinder()
    _GEO = Nominatim(user_agent="facesyma_coach_v1")
except ImportError:
    _KERYKEION_OK = False
    _TF = None
    _GEO = None

log = logging.getLogger(__name__)

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

# generate_coach_sifatlar.py koleksiyon adlarına uygun (ja→jp, ko→kr, es→sp)
_LANG_COL_MAP = {"ja": "jp", "ko": "kr", "es": "sp"}

# Yüz analizi sıfatları (PascalCase, pos_neg DB) → coach arketipi (küçük harf)
# Negatif sıfatlar için büyüme çerçevesi: zayıflık → gelişim fırsatı
FACE_SIFAT_ARCHETYPE: dict[str, str] = {
    # ── Pozitif (42) ────────────────────────────────────────────────────────────
    "Acele_karar_vermeyen":                         "dikkatli",
    "Acik_sozlu":                                   "açık_kalpli",
    "Aile_duskunu_ve_ailesine_onem_veren":          "hassas",
    "Anlayisli":                                    "açık_kalpli",
    "Arkadas_canlisi":                              "sosyal",
    "Bagimsiz_yasamayi_seven":                      "kararlı",
    "Buyuk_resme_odaklanir":                        "lider",
    "Cok_calismaktan_korkmayan":                    "güçlü",
    "Comert":                                       "açık_kalpli",
    "Dengeli_karakter_sahibi":                      "dengeli",
    "Detayci":                                      "analitik",
    "Dominant":                                     "lider",
    "Eglenceye_duskun":                             "enerjik",
    "Etkileyici":                                   "çekici",
    "Gercekci":                                     "pratik",
    "Ikna_edici":                                   "cazip",
    "Ileri_goruslu":                                "lider",
    "Is_ortamini_kontrol_edebilen":                 "lider",
    "Isle_ilgili_kontrol_kendisinde_oldugunda_iyi_calisan": "odaklı",
    "Iyi_kalpli":                                   "açık_kalpli",
    "Kibar":                                        "zarif",
    "Kisa_ve_oz_sozlu":                             "pratik",
    "Kontrolu_elinde_tutma_isteklisi_otoriter":     "lider",
    "Lukse_duskun":                                 "zarif",
    "Motive_edildiginde_basarili_olan":             "odaklı",
    "Mukemmeliyetci":                               "dikkatli",
    "Objektif":                                     "analitik",
    "Odaklanmis":                                   "odaklı",
    "Ongorulu":                                     "analitik",
    "Paylasmayi_seven":                             "sosyal",
    "Planlari_kendisi_yapan":                       "kararlı",
    "Planli":                                       "dikkatli",
    "Samimi_yapiya_sahip":                          "açık_kalpli",
    "Saygili":                                      "zarif",
    "Secici":                                       "dikkatli",
    "Sevdiklerini_koruyucu_ve_sahiplenici":         "hassas",
    "Sistematik":                                   "analitik",
    "Temkinli":                                     "dikkatli",
    "Uretken":                                      "güçlü",
    "Verimli":                                      "odaklı",
    "Zeki":                                         "analitik",
    "İnsanlarin_ruhuna_bakan":                      "sezgisel",
    # ── Negatif → büyüme arketipi (25) ─────────────────────────────────────────
    "Ani_karar_veren":                              "kararlı",    # dürtüsel → kararlı
    "Anlayissiz":                                   "hassas",     # anlayışsız → duyarlılık gelişimi
    "Bencil":                                       "lider",      # öz-odaklı → liderlik büyümesi
    "Cabuk_sinirlenen":                             "güçlü",      # öfkeli → gücü kanalize et
    "Cahil":                                        "yaratıcı",   # bilgisiz → merak/yaratıcılık
    "Dusuncelere_dalip_giden":                      "sezgisel",   # hayalci → sezgisel
    "Duygularini_dusuncelerinin_onunde_tutan":      "hassas",     # duygusal → empati büyümesi
    "Gosteris_meraklisi":                           "cazip",      # gösterişçi → özgün çekicilik
    "Guven_vermeyen":                               "güvenilir",  # güvensiz → güvenilirlik büyümesi
    "Hazci":                                        "enerjik",    # hazcu → enerjiyi yönlendir
    "Iskolik":                                      "odaklı",     # iş bağımlısı → dengeli odak
    "Kaba":                                         "kararlı",    # kaba → doğrudanlık büyümesi
    "Kiskanc":                                      "kararlı",    # kıskanç → hırsı yönlendir
    "Kolay_kontrol_edilen":                         "dengeli",    # manipüle edilebilir → denge büyümesi
    "Korkak_davranmaya_egilimli":                   "güçlü",      # korkak → cesaret büyümesi
    "Kural_disina_cikmaya_yatkin":                  "yaratıcı",   # kural karşıtı → yaratıcılık
    "Oyuncudan_cok_izleyici":                       "güçlü",      # pasif → aktif büyüme
    "Sabirsiz":                                     "enerjik",    # sabırsız → enerjiyi kanalize et
    "Simarik":                                      "zarif",      # şımarık → takdir/zarafet büyümesi
    "Sonuc_odakli":                                 "odaklı",     # sonuç odaklı → odaklı
    "Supheci":                                      "analitik",   # şüpheci → analize dönüştür
    "Tepeden_bakan":                                "lider",      # küçümseyen → gerçek liderlik
    "Uyusuk":                                       "enerjik",    # tembel → enerji aktivasyonu
    "Zamani_iyi_yonetemeyen":                       "dikkatli",   # zaman yönetememe → dikkatli büyüme
    "Zayif_karakterli":                             "güçlü",      # zayıf karakter → güç büyümesi
    # ── Tarafsız (1) ────────────────────────────────────────────────────────────
    "Denetimsiz":                                   "dengeli",    # kontrolsüz → denge büyümesi
}

def _normalize_sifat(sifat: str) -> str:
    """Yüz analizi sıfatını (PascalCase) coach arketipine çevirir.
    Eşleşme yoksa küçük harfe dönüştürür (21 arketiple direkt eşleşme için).
    """
    return FACE_SIFAT_ARCHETYPE.get(sifat, sifat.lower())

_RE_SIFAT = re.compile(r'^[a-zA-ZçğıöşüÇĞİÖŞÜ0-9 _-]{1,100}$')

COACH_MODULES = [
    "saglik_esenwlik", "dogruluk_sadakat", "guvenlik", "suc_egilim",
    "iliski_yonetimi", "iletisim_becerileri", "stres_yonetimi", "ozguven",
    "zaman_yonetimi", "kisisel_hedefler", "astroloji_harita", "dogum_analizi",
    "yas_koc_ozet", "vucut_dil",
    # Tip A — text modüller
    "etkinlik_tavsiye", "spor_aktivite", "kariyer_yolu",
    "insan_kaynaklari", "duygusal_ruhsal", "meditasyon_egzersiz",
    # Tip B — dict/JSON modüller
    "kitap_tavsiye", "film_tavsiye", "muzik_tavsiye",
    "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon", "saglik_tavsiye",
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
    "yas_koc_ozet":          "Yaşam Koçu Genel Özeti",
    "vucut_dil":             "Beden Dili Analizi",
    "etkinlik_tavsiye":      "Etkinlik ve Aktivite Tavsiyeleri",
    "spor_aktivite":         "Spor ve Fiziksel Aktivite",
    "kariyer_yolu":          "Kariyer Yolu Profili",
    "insan_kaynaklari":      "İnsan Kaynakları ve Takım Dinamiği",
    "duygusal_ruhsal":       "Duygusal ve Ruhsal Gelişim",
    "meditasyon_egzersiz":   "Meditasyon ve Mindfulness",
    "kitap_tavsiye":         "Kitap Tavsiyeleri",
    "film_tavsiye":          "Film ve Dizi Tavsiyeleri",
    "muzik_tavsiye":         "Müzik Tavsiyeleri",
    "podcast_tavsiye":       "Podcast Tavsiyeleri",
    "seyahat_tavsiye":       "Seyahat Tavsiyeleri",
    "gunluk_afirasyon":      "Günlük Afirmasyonlar",
    "saglik_tavsiye":        "Sağlık Tavsiyeleri (Yapılandırılmış)",
}

# Sağlık onayı gerektiren modüller
HEALTH_MODULES = frozenset({
    "saglik_tavsiye", "saglik_esenwlik", "meditasyon_egzersiz", "spor_aktivite",
})

# 18 dil medikal sorumluluk reddi + GDPR veri işleme bildirimi
_HEALTH_DISCLAIMER = {
    "tr": "Bu içerik yalnızca bilgilendirme amaçlıdır ve tıbbi tavsiye yerine geçmez. Kişilik analizinizden türetilen bu öneriler yapay zeka tarafından oluşturulmuştur. Sağlık kararları için lütfen bir sağlık uzmanına danışın.",
    "en": "This content is for informational purposes only and does not constitute medical advice. These recommendations are AI-generated based on your personality analysis. Please consult a healthcare professional for medical decisions.",
    "de": "Dieser Inhalt dient nur zu Informationszwecken und stellt keine medizinische Beratung dar. Diese Empfehlungen wurden von einer KI basierend auf Ihrer Persönlichkeitsanalyse erstellt. Bitte konsultieren Sie einen Arzt für medizinische Entscheidungen.",
    "ru": "Этот контент предназначен только для информационных целей и не является медицинской консультацией. Эти рекомендации созданы ИИ на основе анализа вашей личности. Пожалуйста, проконсультируйтесь с врачом по медицинским вопросам.",
    "ar": "هذا المحتوى لأغراض إعلامية فقط ولا يُعدّ نصيحة طبية. هذه التوصيات مُولَّدة بالذكاء الاصطناعي بناءً على تحليل شخصيتك. يُرجى استشارة متخصص رعاية صحية لاتخاذ القرارات الطبية.",
    "es": "Este contenido es solo informativo y no constituye asesoramiento médico. Estas recomendaciones son generadas por IA basándose en tu análisis de personalidad. Consulta a un profesional de la salud para decisiones médicas.",
    "ko": "이 콘텐츠는 정보 제공 목적으로만 제공되며 의료 조언을 대체하지 않습니다. 이 권장 사항은 귀하의 성격 분석을 기반으로 AI가 생성했습니다. 의료 결정을 위해 의료 전문가와 상담하십시오.",
    "ja": "このコンテンツは情報提供のみを目的としており、医療上のアドバイスの代わりにはなりません。これらの推奨事項はあなたの性格分析に基づいてAIが生成したものです。医療上の判断については医療専門家にご相談ください。",
    "zh": "本内容仅供参考，不构成医疗建议。这些建议由人工智能根据您的性格分析生成。请咨询医疗专业人员以作出医疗决定。",
    "hi": "यह सामग्री केवल सूचना के उद्देश्य से है और चिकित्सा सलाह का विकल्प नहीं है। ये सिफारिशें आपके व्यक्तित्व विश्लेषण के आधार पर AI द्वारा उत्पन्न की गई हैं। चिकित्सा निर्णयों के लिए कृपया किसी स्वास्थ्य पेशेवर से परामर्श करें।",
    "fr": "Ce contenu est uniquement à titre informatif et ne constitue pas un avis médical. Ces recommandations sont générées par IA sur la base de votre analyse de personnalité. Veuillez consulter un professionnel de santé pour toute décision médicale.",
    "pt": "Este conteúdo é apenas para fins informativos e não constitui aconselhamento médico. Estas recomendações são geradas por IA com base na sua análise de personalidade. Consulte um profissional de saúde para decisões médicas.",
    "bn": "এই বিষয়বস্তু শুধুমাত্র তথ্যমূলক উদ্দেশ্যে এবং চিকিৎসা পরামর্শের বিকল্প নয়। এই সুপারিশগুলি আপনার ব্যক্তিত্ব বিশ্লেষণের উপর ভিত্তি করে AI দ্বারা তৈরি। চিকিৎসা সিদ্ধান্তের জন্য একজন স্বাস্থ্যসেবা পেশাদারের সাথে পরামর্শ করুন।",
    "id": "Konten ini hanya untuk tujuan informasi dan bukan merupakan saran medis. Rekomendasi ini dihasilkan oleh AI berdasarkan analisis kepribadian Anda. Konsultasikan dengan profesional kesehatan untuk keputusan medis.",
    "ur": "یہ مواد صرف معلوماتی مقاصد کے لیے ہے اور طبی مشورے کا متبادل نہیں ہے۔ یہ تجاویز آپ کی شخصیت کے تجزیے کی بنیاد پر AI نے تیار کی ہیں۔ طبی فیصلوں کے لیے براہ کرم کسی صحت پیشہ ور سے مشورہ کریں۔",
    "it": "Questo contenuto è solo a scopo informativo e non costituisce un consiglio medico. Queste raccomandazioni sono generate dall'IA in base alla tua analisi della personalità. Si prega di consultare un professionista sanitario per le decisioni mediche.",
    "vi": "Nội dung này chỉ mang tính chất thông tin và không thay thế lời khuyên y tế. Các khuyến nghị này được AI tạo ra dựa trên phân tích tính cách của bạn. Vui lòng tham khảo ý kiến chuyên gia y tế để đưa ra quyết định về sức khỏe.",
    "pl": "Ta treść służy wyłącznie celom informacyjnym i nie stanowi porady medycznej. Te zalecenia są generowane przez AI na podstawie analizy Twojej osobowości. Skonsultuj się z pracownikiem służby zdrowia w sprawie decyzji medycznych.",
}
_HEALTH_DISCLAIMER_VERSION = "v1"

def _get_disclaimer(lang: str) -> dict:
    text = _HEALTH_DISCLAIMER.get(lang) or _HEALTH_DISCLAIMER["en"]
    return {"text": text, "version": _HEALTH_DISCLAIMER_VERSION, "requires_consent": True}

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

def get_main_db():
    return _get_client()["facesyma-backend"]


def _fetch_user_memories(user_id: int) -> list:
    """Pull long-term memories from ai_user_memory (best-effort, returns [] on error)."""
    if not user_id:
        return []
    try:
        doc = get_main_db()["ai_user_memory"].find_one(
            {"user_id": user_id}, {"_id": 0, "memories": 1}
        )
        return (doc or {}).get("memories", [])[-12:]  # max 12 recent
    except Exception as e:
        log.warning(f"_fetch_user_memories failed for {user_id}: {e}")
        return []

# ── Yüz × Doğum örtüşme analizi ──────────────────────────────────────────────

# Her burç için beklenen kişilik arketipleri (FACE_SIFAT_ARCHETYPE değerleriyle eşleşir)
_SIGN_ARCHETYPES: dict[str, frozenset] = {
    'Aries':       frozenset(['lider', 'enerjik', 'güçlü', 'kararlı']),
    'Taurus':      frozenset(['güvenilir', 'pratik', 'odaklı', 'dengeli']),
    'Gemini':      frozenset(['sosyal', 'analitik', 'enerjik', 'çekici']),
    'Cancer':      frozenset(['hassas', 'açık_kalpli', 'güvenilir', 'sezgisel']),
    'Leo':         frozenset(['lider', 'enerjik', 'güçlü', 'çekici']),
    'Virgo':       frozenset(['analitik', 'dikkatli', 'pratik', 'odaklı']),
    'Libra':       frozenset(['dengeli', 'sosyal', 'zarif', 'açık_kalpli']),
    'Scorpio':     frozenset(['kararlı', 'güçlü', 'analitik', 'sezgisel']),
    'Sagittarius': frozenset(['enerjik', 'sosyal', 'güçlü', 'kararlı']),
    'Capricorn':   frozenset(['kararlı', 'analitik', 'güvenilir', 'odaklı']),
    'Aquarius':    frozenset(['yaratıcı', 'sosyal', 'analitik', 'açık_kalpli']),
    'Pisces':      frozenset(['hassas', 'yaratıcı', 'açık_kalpli', 'sezgisel']),
}

_ARCHETYPE_LABELS: dict[str, dict] = {
    'tr': {
        'dikkatli': 'Dikkatli', 'açık_kalpli': 'Açık Kalpli', 'hassas': 'Hassas',
        'sosyal': 'Sosyal', 'kararlı': 'Kararlı', 'lider': 'Lider',
        'güçlü': 'Güçlü', 'enerjik': 'Enerjik', 'çekici': 'Çekici',
        'pratik': 'Pratik', 'cazip': 'Cazip', 'odaklı': 'Odaklı',
        'zarif': 'Zarif', 'analitik': 'Analitik', 'dengeli': 'Dengeli',
        'yaratıcı': 'Yaratıcı', 'güvenilir': 'Güvenilir', 'sezgisel': 'Sezgisel',
    },
    'en': {
        'dikkatli': 'Careful', 'açık_kalpli': 'Open-hearted', 'hassas': 'Sensitive',
        'sosyal': 'Social', 'kararlı': 'Determined', 'lider': 'Leader',
        'güçlü': 'Strong', 'enerjik': 'Energetic', 'çekici': 'Attractive',
        'pratik': 'Practical', 'cazip': 'Charming', 'odaklı': 'Focused',
        'zarif': 'Elegant', 'analitik': 'Analytical', 'dengeli': 'Balanced',
        'yaratıcı': 'Creative', 'güvenilir': 'Reliable', 'sezgisel': 'Intuitive',
    },
    'de': {
        'dikkatli': 'Sorgfältig', 'açık_kalpli': 'Aufgeschlossen', 'hassas': 'Sensibel',
        'sosyal': 'Sozial', 'kararlı': 'Entschlossen', 'lider': 'Anführer',
        'güçlü': 'Stark', 'enerjik': 'Energetisch', 'çekici': 'Attraktiv',
        'pratik': 'Praktisch', 'cazip': 'Charmant', 'odaklı': 'Fokussiert',
        'zarif': 'Elegant', 'analitik': 'Analytisch', 'dengeli': 'Ausgeglichen',
        'yaratıcı': 'Kreativ', 'güvenilir': 'Zuverlässig', 'sezgisel': 'Intuitiv',
    },
    'ru': {
        'dikkatli': 'Внимательный', 'açık_kalpli': 'Открытый', 'hassas': 'Чуткий',
        'sosyal': 'Общительный', 'kararlı': 'Решительный', 'lider': 'Лидер',
        'güçlü': 'Сильный', 'enerjik': 'Энергичный', 'çekici': 'Привлекательный',
        'pratik': 'Практичный', 'cazip': 'Обаятельный', 'odaklı': 'Сосредоточенный',
        'zarif': 'Элегантный', 'analitik': 'Аналитический', 'dengeli': 'Сбалансированный',
        'yaratıcı': 'Творческий', 'güvenilir': 'Надёжный', 'sezgisel': 'Интуитивный',
    },
    'ar': {
        'dikkatli': 'دقيق', 'açık_kalpli': 'منفتح', 'hassas': 'حساس',
        'sosyal': 'اجتماعي', 'kararlı': 'حازم', 'lider': 'قائد',
        'güçlü': 'قوي', 'enerjik': 'نشيط', 'çekici': 'جذاب',
        'pratik': 'عملي', 'cazip': 'ساحر', 'odaklı': 'مركّز',
        'zarif': 'أنيق', 'analitik': 'تحليلي', 'dengeli': 'متوازن',
        'yaratıcı': 'مبدع', 'güvenilir': 'موثوق', 'sezgisel': 'حدسي',
    },
    'es': {
        'dikkatli': 'Cuidadoso', 'açık_kalpli': 'Generoso', 'hassas': 'Sensible',
        'sosyal': 'Social', 'kararlı': 'Determinado', 'lider': 'Líder',
        'güçlü': 'Fuerte', 'enerjik': 'Enérgico', 'çekici': 'Atractivo',
        'pratik': 'Práctico', 'cazip': 'Encantador', 'odaklı': 'Enfocado',
        'zarif': 'Elegante', 'analitik': 'Analítico', 'dengeli': 'Equilibrado',
        'yaratıcı': 'Creativo', 'güvenilir': 'Confiable', 'sezgisel': 'Intuitivo',
    },
    'ko': {
        'dikkatli': '신중한', 'açık_kalpli': '열린 마음', 'hassas': '민감한',
        'sosyal': '사교적인', 'kararlı': '결단력 있는', 'lider': '리더',
        'güçlü': '강인한', 'enerjik': '활력 있는', 'çekici': '매력적인',
        'pratik': '실용적인', 'cazip': '매혹적인', 'odaklı': '집중력 있는',
        'zarif': '우아한', 'analitik': '분석적인', 'dengeli': '균형 잡힌',
        'yaratıcı': '창의적인', 'güvenilir': '신뢰할 수 있는', 'sezgisel': '직관적인',
    },
    'ja': {
        'dikkatli': '慎重', 'açık_kalpli': '開放的', 'hassas': '繊細',
        'sosyal': '社交的', 'kararlı': '決断力がある', 'lider': 'リーダー',
        'güçlü': '強い', 'enerjik': 'エネルギッシュ', 'çekici': '魅力的',
        'pratik': '実用的', 'cazip': 'チャーミング', 'odaklı': '集中力がある',
        'zarif': 'エレガント', 'analitik': '分析的', 'dengeli': 'バランスが取れている',
        'yaratıcı': '創造的', 'güvenilir': '信頼できる', 'sezgisel': '直感的',
    },
    'zh': {
        'dikkatli': '谨慎', 'açık_kalpli': '开朗', 'hassas': '敏感',
        'sosyal': '社交', 'kararlı': '果断', 'lider': '领袖',
        'güçlü': '强大', 'enerjik': '充满活力', 'çekici': '有魅力',
        'pratik': '务实', 'cazip': '迷人', 'odaklı': '专注',
        'zarif': '优雅', 'analitik': '分析型', 'dengeli': '平衡',
        'yaratıcı': '创造力', 'güvenilir': '可靠', 'sezgisel': '直觉',
    },
    'hi': {
        'dikkatli': 'सावधान', 'açık_kalpli': 'उदार', 'hassas': 'संवेदनशील',
        'sosyal': 'सामाजिक', 'kararlı': 'दृढ़', 'lider': 'नेता',
        'güçlü': 'शक्तिशाली', 'enerjik': 'ऊर्जावान', 'çekici': 'आकर्षक',
        'pratik': 'व्यावहारिक', 'cazip': 'मनमोहक', 'odaklı': 'केंद्रित',
        'zarif': 'सुरुचिपूर्ण', 'analitik': 'विश्लेषणात्मक', 'dengeli': 'संतुलित',
        'yaratıcı': 'रचनात्मक', 'güvenilir': 'विश्वसनीय', 'sezgisel': 'सहज',
    },
    'fr': {
        'dikkatli': 'Attentionné', 'açık_kalpli': "Ouvert d'esprit", 'hassas': 'Sensible',
        'sosyal': 'Sociable', 'kararlı': 'Déterminé', 'lider': 'Leader',
        'güçlü': 'Fort', 'enerjik': 'Énergique', 'çekici': 'Attrayant',
        'pratik': 'Pratique', 'cazip': 'Charmant', 'odaklı': 'Concentré',
        'zarif': 'Élégant', 'analitik': 'Analytique', 'dengeli': 'Équilibré',
        'yaratıcı': 'Créatif', 'güvenilir': 'Fiable', 'sezgisel': 'Intuitif',
    },
    'pt': {
        'dikkatli': 'Cuidadoso', 'açık_kalpli': 'Generoso', 'hassas': 'Sensível',
        'sosyal': 'Social', 'kararlı': 'Determinado', 'lider': 'Líder',
        'güçlü': 'Forte', 'enerjik': 'Enérgico', 'çekici': 'Atraente',
        'pratik': 'Prático', 'cazip': 'Encantador', 'odaklı': 'Focado',
        'zarif': 'Elegante', 'analitik': 'Analítico', 'dengeli': 'Equilibrado',
        'yaratıcı': 'Criativo', 'güvenilir': 'Confiável', 'sezgisel': 'Intuitivo',
    },
    'bn': {
        'dikkatli': 'সতর্ক', 'açık_kalpli': 'উদার', 'hassas': 'সংবেদনশীল',
        'sosyal': 'সামাজিক', 'kararlı': 'দৃঢ়প্রতিজ্ঞ', 'lider': 'নেতা',
        'güçlü': 'শক্তিশালী', 'enerjik': 'উদ্যমী', 'çekici': 'আকর্ষণীয়',
        'pratik': 'বাস্তববাদী', 'cazip': 'মনোমুগ্ধকর', 'odaklı': 'মনোযোগী',
        'zarif': 'মার্জিত', 'analitik': 'বিশ্লেষণাত্মক', 'dengeli': 'ভারসাম্যপূর্ণ',
        'yaratıcı': 'সৃজনশীল', 'güvenilir': 'নির্ভরযোগ্য', 'sezgisel': 'স্বজ্ঞাত',
    },
    'id': {
        'dikkatli': 'Teliti', 'açık_kalpli': 'Tulus', 'hassas': 'Sensitif',
        'sosyal': 'Sosial', 'kararlı': 'Teguh', 'lider': 'Pemimpin',
        'güçlü': 'Kuat', 'enerjik': 'Energik', 'çekici': 'Menarik',
        'pratik': 'Praktis', 'cazip': 'Memesona', 'odaklı': 'Fokus',
        'zarif': 'Anggun', 'analitik': 'Analitis', 'dengeli': 'Seimbang',
        'yaratıcı': 'Kreatif', 'güvenilir': 'Dapat Diandalkan', 'sezgisel': 'Intuitif',
    },
    'ur': {
        'dikkatli': 'محتاط', 'açık_kalpli': 'کھلے دل کا', 'hassas': 'حساس',
        'sosyal': 'ملنسار', 'kararlı': 'پرعزم', 'lider': 'رہنما',
        'güçlü': 'طاقتور', 'enerjik': 'توانا', 'çekici': 'پرکشش',
        'pratik': 'عملی', 'cazip': 'دلکش', 'odaklı': 'متمرکز',
        'zarif': 'خوش اطوار', 'analitik': 'تجزیاتی', 'dengeli': 'متوازن',
        'yaratıcı': 'تخلیقی', 'güvenilir': 'قابل اعتماد', 'sezgisel': 'بدیہی',
    },
    'it': {
        'dikkatli': 'Attento', 'açık_kalpli': 'Generoso', 'hassas': 'Sensibile',
        'sosyal': 'Socievole', 'kararlı': 'Determinato', 'lider': 'Leader',
        'güçlü': 'Forte', 'enerjik': 'Energico', 'çekici': 'Attraente',
        'pratik': 'Pratico', 'cazip': 'Affascinante', 'odaklı': 'Concentrato',
        'zarif': 'Elegante', 'analitik': 'Analitico', 'dengeli': 'Equilibrato',
        'yaratıcı': 'Creativo', 'güvenilir': 'Affidabile', 'sezgisel': 'Intuitivo',
    },
    'vi': {
        'dikkatli': 'Cẩn thận', 'açık_kalpli': 'Rộng lượng', 'hassas': 'Nhạy cảm',
        'sosyal': 'Hòa đồng', 'kararlı': 'Quyết đoán', 'lider': 'Lãnh đạo',
        'güçlü': 'Mạnh mẽ', 'enerjik': 'Năng động', 'çekici': 'Hấp dẫn',
        'pratik': 'Thực tế', 'cazip': 'Cuốn hút', 'odaklı': 'Tập trung',
        'zarif': 'Thanh lịch', 'analitik': 'Phân tích', 'dengeli': 'Cân bằng',
        'yaratıcı': 'Sáng tạo', 'güvenilir': 'Đáng tin cậy', 'sezgisel': 'Trực giác',
    },
    'pl': {
        'dikkatli': 'Uważny', 'açık_kalpli': 'Otwarty', 'hassas': 'Wrażliwy',
        'sosyal': 'Towarzyski', 'kararlı': 'Zdecydowany', 'lider': 'Lider',
        'güçlü': 'Silny', 'enerjik': 'Energiczny', 'çekici': 'Atrakcyjny',
        'pratik': 'Praktyczny', 'cazip': 'Czarujący', 'odaklı': 'Skupiony',
        'zarif': 'Elegancki', 'analitik': 'Analityczny', 'dengeli': 'Zrównoważony',
        'yaratıcı': 'Kreatywny', 'güvenilir': 'Niezawodny', 'sezgisel': 'Intuicyjny',
    },
}

_FACE_ASTRO_SUMMARY: dict[str, dict] = {
    'high': {
        'tr': 'Yüz analizin {sign} burç karakteriyle güçlü örtüşme gösteriyor. Her iki sistem de seni {traits} olarak tanımlıyor.',
        'en': 'Your face analysis shows strong alignment with {sign} traits. Both systems identify you as {traits}.',
        'de': 'Deine Gesichtsanalyse zeigt starke Übereinstimmung mit {sign}. Beide Systeme beschreiben dich als {traits}.',
        'ru': 'Твой анализ лица показывает сильное совпадение с чертами {sign}. Обе системы описывают тебя как {traits}.',
        'ar': 'يُظهر تحليل وجهك توافقاً قوياً مع سمات {sign}. يصفك كلا النظامين بأنك {traits}.',
        'es': 'Tu análisis facial muestra fuerte alineación con los rasgos de {sign}. Ambos sistemas te identifican como {traits}.',
        'ko': '당신의 얼굴 분석은 {sign} 특성과 강한 일치를 보여줍니다. 두 시스템 모두 당신을 {traits}로 식별합니다.',
        'ja': 'あなたの顔分析は{sign}の特性と強い一致を示しています。両方のシステムがあなたを{traits}と識別しています。',
        'zh': '您的面部分析与{sign}特质高度吻合。两个系统都将您定义为{traits}。',
        'hi': 'आपका चेहरा विश्लेषण {sign} विशेषताओं के साथ मजबूत संरेखण दिखाता है। दोनों प्रणालियां आपको {traits} के रूप में पहचानती हैं।',
        'fr': 'Ton analyse faciale montre une forte concordance avec les traits {sign}. Les deux systèmes te décrivent comme {traits}.',
        'pt': 'Sua análise facial mostra forte alinhamento com os traços de {sign}. Ambos os sistemas identificam você como {traits}.',
        'bn': 'আপনার মুখ বিশ্লেষণ {sign} বৈশিষ্ট্যগুলির সাথে শক্তিশালী সংযোগ দেখায়। উভয় সিস্টেম আপনাকে {traits} হিসাবে চিহ্নিত করে।',
        'id': 'Analisis wajahmu menunjukkan kesesuaian kuat dengan sifat {sign}. Kedua sistem mengidentifikasimu sebagai {traits}.',
        'ur': 'آپ کا چہرہ تجزیہ {sign} کی خصوصیات کے ساتھ مضبوط ہم آہنگی ظاہر کرتا ہے۔ دونوں نظام آپ کو {traits} کے طور پر شناخت کرتے ہیں۔',
        'it': 'La tua analisi del viso mostra forte allineamento con i tratti {sign}. Entrambi i sistemi ti descrivono come {traits}.',
        'vi': 'Phân tích khuôn mặt của bạn cho thấy sự phù hợp mạnh mẽ với đặc điểm {sign}. Cả hai hệ thống đều xác định bạn là {traits}.',
        'pl': 'Twoja analiza twarzy wykazuje silną zgodność z cechami {sign}. Oba systemy określają cię jako {traits}.',
    },
    'mid': {
        'tr': 'Yüz analizin {sign} burç karakteriyle kısmen örtüşüyor. {traits} özelliklerin her iki sistemde de öne çıkıyor.',
        'en': 'Your face analysis partly aligns with {sign} traits. {traits} qualities appear in both readings.',
        'de': 'Deine Gesichtsanalyse stimmt teilweise mit {sign} überein. {traits} erscheinen in beiden Lesungen.',
        'ru': 'Твой анализ лица частично совпадает с {sign}. {traits} проявляются в обоих анализах.',
        'ar': 'يتوافق تحليل وجهك جزئياً مع {sign}. تظهر صفات {traits} في كلا القراءتين.',
        'es': 'Tu análisis facial se alinea parcialmente con {sign}. Las cualidades de {traits} aparecen en ambas lecturas.',
        'ko': '당신의 얼굴 분석은 {sign}과 부분적으로 일치합니다. {traits} 특성이 두 분석 모두에서 나타납니다.',
        'ja': 'あなたの顔分析は{sign}と部分的に一致しています。{traits}の特性が両方の分析に現れています。',
        'zh': '您的面部分析与{sign}部分吻合。{traits}特质在两种分析中均有体现。',
        'hi': 'आपका चेहरा विश्लेषण आंशिक रूप से {sign} के साथ संरेखित होता है। {traits} गुण दोनों विश्लेषणों में दिखाई देते हैं।',
        'fr': "Ton analyse faciale s'aligne partiellement avec {sign}. Les qualités {traits} apparaissent dans les deux lectures.",
        'pt': 'Sua análise facial se alinha parcialmente com {sign}. As qualidades de {traits} aparecem em ambas as leituras.',
        'bn': 'আপনার মুখ বিশ্লেষণ আংশিকভাবে {sign} এর সাথে মিলে যায়। {traits} গুণাবলী উভয় পাঠেই দেখা যায়।',
        'id': 'Analisis wajahmu sebagian selaras dengan {sign}. Kualitas {traits} muncul di kedua bacaan.',
        'ur': 'آپ کا چہرہ تجزیہ جزوی طور پر {sign} سے ہم آہنگ ہے۔ {traits} کی خوبیاں دونوں تجزیوں میں ظاہر ہوتی ہیں۔',
        'it': 'La tua analisi del viso si allinea parzialmente con {sign}. Le qualità {traits} appaiono in entrambe le letture.',
        'vi': 'Phân tích khuôn mặt của bạn phù hợp một phần với {sign}. Phẩm chất {traits} xuất hiện trong cả hai bài đọc.',
        'pl': 'Twoja analiza twarzy częściowo pokrywa się z {sign}. Cechy {traits} pojawiają się w obu odczytach.',
    },
    'low': {
        'tr': 'Yüz analizin {sign} burç karakteriyle farklı özellikler öne çıkarıyor — bu ilginç bir kontrast. Yüzün {traits} vurgularken burç farklı bir enerji getiriyor.',
        'en': 'Your face analysis highlights different qualities from {sign} — an interesting contrast. Your face emphasizes {traits} while your sign brings different energy.',
        'de': 'Deine Gesichtsanalyse hebt andere Qualitäten als {sign} hervor — ein interessanter Kontrast. Dein Gesicht betont {traits}, während dein Zeichen andere Energie bringt.',
        'ru': 'Твой анализ лица выделяет другие качества, чем {sign} — интересный контраст. Лицо подчёркивает {traits}, а знак несёт другую энергию.',
        'ar': 'يبرز تحليل وجهك صفات مختلفة عن {sign} — تناقض مثير للاهتمام. يؤكد وجهك {traits} بينما يجلب برجك طاقة مختلفة.',
        'es': 'Tu análisis facial destaca cualidades diferentes de {sign} — un interesante contraste. Tu rostro enfatiza {traits} mientras tu signo aporta energía diferente.',
        'ko': '당신의 얼굴 분석은 {sign}과 다른 특성을 강조합니다 — 흥미로운 대조입니다. 얼굴은 {traits}를 강조하고 별자리는 다른 에너지를 가져옵니다.',
        'ja': 'あなたの顔分析は{sign}とは異なる特性を強調しています — 興味深い対比です。顔は{traits}を強調し、星座は異なるエネルギーをもたらします。',
        'zh': '您的面部分析突出了与{sign}不同的特质——这是一个有趣的对比。您的面部强调{traits}，而星座带来了不同的能量。',
        'hi': 'आपका चेहरा विश्लेषण {sign} से अलग गुणों पर जोर देता है — एक दिलचस्प विरोधाभास। आपका चेहरा {traits} पर जोर देता है जबकि राशि अलग ऊर्जा लाती है।',
        'fr': "Ton analyse faciale met en avant des qualités différentes de {sign} — un contraste intéressant. Ton visage souligne {traits} tandis que ton signe apporte une énergie différente.",
        'pt': 'Sua análise facial destaca qualidades diferentes de {sign} — um contraste interessante. Seu rosto enfatiza {traits} enquanto seu signo traz energia diferente.',
        'bn': 'আপনার মুখ বিশ্লেষণ {sign} থেকে আলাদা গুণাবলী তুলে ধরে — একটি আকর্ষণীয় বৈপরীত্য। আপনার মুখ {traits} জোর দেয় যখন আপনার রাশি ভিন্ন শক্তি আনে।',
        'id': 'Analisis wajahmu menonjolkan kualitas berbeda dari {sign} — kontras yang menarik. Wajahmu menekankan {traits} sementara tandamu membawa energi berbeda.',
        'ur': 'آپ کا چہرہ تجزیہ {sign} سے مختلف خوبیاں اجاگر کرتا ہے — ایک دلچسپ تضاد۔ آپ کا چہرہ {traits} پر زور دیتا ہے جبکہ برج مختلف توانائی لاتا ہے۔',
        'it': 'La tua analisi del viso evidenzia qualità diverse da {sign} — un contrasto interessante. Il tuo viso enfatizza {traits} mentre il tuo segno porta energia diversa.',
        'vi': 'Phân tích khuôn mặt của bạn nổi bật các phẩm chất khác với {sign} — một sự tương phản thú vị. Khuôn mặt bạn nhấn mạnh {traits} trong khi cung hoàng đạo mang lại năng lượng khác.',
        'pl': 'Twoja analiza twarzy podkreśla inne cechy niż {sign} — interesujący kontrast. Twarz akcentuje {traits}, podczas gdy twój znak przynosi inną energię.',
    },
}

_FACE_ASTRO_TITLE: dict[str, str] = {
    'tr': 'Yüz & Doğum Örtüşmesi',
    'en': 'Face & Birth Alignment',
    'de': 'Gesicht & Geburts-Übereinstimmung',
    'ru': 'Соответствие лица и рождения',
    'ar': 'تطابق الوجه والميلاد',
    'es': 'Alineación Cara & Nacimiento',
    'ko': '얼굴 & 출생 일치',
    'ja': '顔と誕生の一致',
    'zh': '面部与出生对应',
    'hi': 'चेहरा और जन्म संरेखण',
    'fr': 'Alignement Visage & Naissance',
    'pt': 'Alinhamento Rosto & Nascimento',
    'bn': 'মুখ ও জন্ম সংযোগ',
    'id': 'Keselarasan Wajah & Kelahiran',
    'ur': 'چہرے اور پیدائش کی ہم آہنگی',
    'it': 'Allineamento Viso & Nascita',
    'vi': 'Sự Trùng Hợp Khuôn Mặt & Ngày Sinh',
    'pl': 'Dopasowanie Twarzy i Urodzin',
}


def _get_user_face_sifatlar(user_id: int) -> list:
    """Kullanıcının son enhanced_character analizinden top_sifatlar listesini döndürür."""
    try:
        doc = get_source()['analysis_history'].find_one(
            {'user_id': user_id, 'mode': 'enhanced_character'},
            sort=[('created_at', -1)],
            projection={'result.top_sifatlar': 1, 'result.positive_sifatlar': 1, '_id': 0},
        )
        if not doc:
            return []
        result = doc.get('result', {})
        return (result.get('top_sifatlar') or result.get('positive_sifatlar') or [])[:10]
    except Exception:
        return []


def _build_face_astro_match(english_sign: str, sign_label: str, face_sifatlar: list, lang: str) -> dict:
    """
    Yüz sıfatlarını burç arketipleriyle karşılaştırır.
    english_sign: 'Aries', 'Leo' gibi İngilizce burç adı (_SIGN_ARCHETYPES key'leriyle eşleşir)
    sign_label:   Kullanıcının dilinde burç adı (gösterim için)
    face_sifatlar: [{'sifat': str, 'score': float}, ...]
    """
    if not english_sign or not face_sifatlar:
        return {'has_face_data': False}

    sign_archetypes = _SIGN_ARCHETYPES.get(english_sign, frozenset())
    lang_key = lang if lang in _ARCHETYPE_LABELS else 'en'
    label_map = _ARCHETYPE_LABELS.get(lang_key, _ARCHETYPE_LABELS['en'])

    # Yüz sıfatlarını arketipe çevir
    face_archetypes: list[str] = []
    for item in face_sifatlar:
        sifat = item.get('sifat', '') if isinstance(item, dict) else str(item)
        archetype = FACE_SIFAT_ARCHETYPE.get(sifat, sifat.lower())
        if archetype and archetype not in face_archetypes:
            face_archetypes.append(archetype)

    # Örtüşen arketipler
    confirming = [a for a in face_archetypes if a in sign_archetypes]
    match_score = round(len(confirming) / len(sign_archetypes) * 100) if sign_archetypes else 0

    # Özet metin
    if confirming:
        traits_str = ', '.join(label_map.get(a, a) for a in confirming[:3])
    else:
        traits_str = ', '.join(label_map.get(a, a) for a in list(face_archetypes)[:2]) if face_archetypes else '—'

    level = 'high' if match_score >= 75 else ('mid' if match_score >= 40 else 'low')
    summary_tmpl = _FACE_ASTRO_SUMMARY[level].get(lang_key, _FACE_ASTRO_SUMMARY[level]['en'])
    summary = summary_tmpl.format(sign=sign_label, traits=traits_str)

    title = _FACE_ASTRO_TITLE.get(lang, _FACE_ASTRO_TITLE['en'])

    return {
        'has_face_data': True,
        'title': title,
        'match_score': match_score,
        'confirming_traits': [label_map.get(a, a) for a in confirming],
        'face_top_archetypes': [label_map.get(a, a) for a in face_archetypes[:5]],
        'summary': summary,
    }


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
    name:           Optional[str]  = None   # İsim analizi için (opsiyonel)
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
    test_scores:     Optional[dict] = None   # {test_type: {domain: score 0-100}}
    user_memories:   Optional[List[dict]] = None  # from GET /chat/memories

class GiyimRequest(BaseModel):
    analysis_result: dict           # /analyze/enhanced/ çıktısı
    lang:            str = "tr"
    mevsim:          Optional[str] = None    # ilkbahar|yaz|sonbahar|kis
    kategori:        Optional[str] = None    # gunluk|spor|resmi|davet
    top_n:           int = 3

_TEST_MODULE_HINTS: list[tuple[str, str, float, str]] = [
    # ── Personality (Big Five) ─────────────────────────────────────────────────
    ("personality", "neuroticism",       65.0, "stres_yonetimi"),
    ("personality", "neuroticism",       65.0, "meditasyon_egzersiz"),
    ("personality", "conscientiousness", 65.0, "zaman_yonetimi"),
    ("personality", "extraversion",      40.0, "iletisim_becerileri"),   # low
    ("personality", "extraversion",      40.0, "etkinlik_tavsiye"),      # low
    ("personality", "openness",          65.0, "kitap_tavsiye"),
    ("personality", "openness",          65.0, "film_tavsiye"),
    ("personality", "openness",          65.0, "muzik_tavsiye"),
    ("personality", "agreeableness",     40.0, "iliski_yonetimi"),       # low

    # ── Skills ────────────────────────────────────────────────────────────────
    ("skills", "problem_solving",  40.0, "kariyer_yolu"),               # low
    ("skills", "empathy",          40.0, "iliski_yonetimi"),            # low
    ("skills", "organization",     40.0, "zaman_yonetimi"),             # low
    ("skills", "learning_speed",   65.0, "kitap_tavsiye"),
    ("skills", "learning_speed",   65.0, "podcast_tavsiye"),
    ("skills", "decision_making",  40.0, "insan_kaynaklari"),           # low

    # ── HR ────────────────────────────────────────────────────────────────────
    ("hr", "leadership",       65.0, "kariyer_yolu"),
    ("hr", "leadership",       65.0, "insan_kaynaklari"),
    ("hr", "team_fit",         40.0, "iletisim_becerileri"),            # low
    ("hr", "stress_tolerance", 40.0, "stres_yonetimi"),                 # low
    ("hr", "stress_tolerance", 40.0, "meditasyon_egzersiz"),            # low
    ("hr", "motivation",       40.0, "gunluk_afirasyon"),               # low
    ("hr", "motivation",       40.0, "kariyer_yolu"),                   # low

    # ── Career ────────────────────────────────────────────────────────────────
    ("career", "creative",       65.0, "film_tavsiye"),
    ("career", "creative",       65.0, "muzik_tavsiye"),
    ("career", "creative",       65.0, "kitap_tavsiye"),
    ("career", "social",         65.0, "etkinlik_tavsiye"),
    ("career", "entrepreneurial",65.0, "kariyer_yolu"),
    ("career", "managerial",     65.0, "insan_kaynaklari"),
    ("career", "analytical",     65.0, "podcast_tavsiye"),
    ("career", "technical",      65.0, "kariyer_yolu"),

    # ── Vocation (Holland RIASEC) ─────────────────────────────────────────────
    ("vocation", "artistic",      65.0, "film_tavsiye"),
    ("vocation", "artistic",      65.0, "muzik_tavsiye"),
    ("vocation", "artistic",      65.0, "kitap_tavsiye"),
    ("vocation", "social",        65.0, "etkinlik_tavsiye"),
    ("vocation", "realistic",     65.0, "spor_aktivite"),
    ("vocation", "investigative", 65.0, "podcast_tavsiye"),
    ("vocation", "enterprising",  65.0, "kariyer_yolu"),

    # ── Relationship ──────────────────────────────────────────────────────────
    ("relationship", "emotional_intelligence", 40.0, "duygusal_ruhsal"), # low
    ("relationship", "emotional_intelligence", 40.0, "iliski_yonetimi"), # low
    ("relationship", "relationship_values",    40.0, "iliski_yonetimi"), # low

    # ── Attachment ────────────────────────────────────────────────────────────
    ("attachment", "anxiety",   65.0, "duygusal_ruhsal"),
    ("attachment", "anxiety",   65.0, "meditasyon_egzersiz"),
    ("attachment", "avoidance", 65.0, "iliski_yonetimi"),

    # ── Grit ──────────────────────────────────────────────────────────────────
    ("grit", "perseverance", 40.0, "gunluk_afirasyon"),                  # low
    ("grit", "perseverance", 40.0, "kariyer_yolu"),                      # low
    ("grit", "passion",      65.0, "kariyer_yolu"),

    # ── Growth mindset ────────────────────────────────────────────────────────
    ("growth_mindset", "growth_mindset", 65.0, "kitap_tavsiye"),
    ("growth_mindset", "growth_mindset", 65.0, "podcast_tavsiye"),

    # ── Self-compassion ───────────────────────────────────────────────────────
    ("self_compassion", "mindfulness",       40.0, "meditasyon_egzersiz"), # low
    ("self_compassion", "self_kindness",     40.0, "gunluk_afirasyon"),    # low
    ("self_compassion", "isolation",         65.0, "etkinlik_tavsiye"),
    ("self_compassion", "isolation",         65.0, "seyahat_tavsiye"),
    ("self_compassion", "self_judgment",     65.0, "duygusal_ruhsal"),
    ("self_compassion", "overidentification",65.0, "stres_yonetimi"),

    # ── Body image ────────────────────────────────────────────────────────────
    ("body_image", "body_satisfaction",    40.0, "saglik_tavsiye"),       # low
    ("body_image", "body_satisfaction",    40.0, "spor_aktivite"),        # low
    ("body_image", "appearance_evaluation",40.0, "ozguven"),              # low

    # ── Self-efficacy & Stress ────────────────────────────────────────────────
    ("self_efficacy", "self_efficacy", 40.0, "ozguven"),                  # low
    ("self_efficacy", "self_efficacy", 40.0, "kariyer_yolu"),             # low
    ("stress",        "depression",    40.0, "duygusal_ruhsal"),          # low
    ("stress",        "anxiety",       40.0, "stres_yonetimi"),           # low
    ("stress",        "depression",    60.0, "meditasyon_egzersiz"),

    # ── Life satisfaction ─────────────────────────────────────────────────────
    ("life_satisfaction", "life_satisfaction", 40.0, "gunluk_afirasyon"), # low
    ("life_satisfaction", "life_satisfaction", 40.0, "seyahat_tavsiye"),  # low

    # ── EQ & nonverbal ───────────────────────────────────────────────────────
    ("eq",                "empathy",             40.0, "iliski_yonetimi"),
    ("eq",                "self_awareness",       40.0, "ozguven"),
    ("eq",                "self_regulation",      40.0, "stres_yonetimi"),
    ("emotion_recognition","overall",             60.0, "iletisim_becerileri"),
    ("emotion_recognition","overall",             60.0, "iliski_yonetimi"),
    ("stroop",             "cognitive_flexibility",50.0, "stres_yonetimi"),
    ("stroop",             "cognitive_flexibility",50.0, "zaman_yonetimi"),
]

# Domains where LOW score triggers the hint (below threshold)
_LOW_SCORE_DOMAINS = {
    # personality
    "extraversion", "agreeableness",
    # skills / hr
    "empathy", "organization", "problem_solving", "decision_making", "team_fit", "stress_tolerance", "motivation",
    # relationship / attachment
    "emotional_intelligence", "relationship_values", "anxiety", "avoidance",
    # self-compassion
    "mindfulness", "self_kindness",
    # body image / self-efficacy / life-sat / grit
    "body_satisfaction", "appearance_evaluation", "self_efficacy", "life_satisfaction", "perseverance",
    # EQ / stress
    "self_awareness", "self_regulation", "depression",
    # nonverbal
    "overall", "cognitive_flexibility",
}


def _test_scores_to_insights(test_scores: dict) -> tuple[list[str], dict]:
    """Puan eşiklerinden koç modülü önerileri ve içgörüler üretir."""
    suggested: list[str] = []
    insights: dict = {}

    for ttype, domain, threshold, module in _TEST_MODULE_HINTS:
        scores = test_scores.get(ttype, {})
        if domain not in scores:
            continue
        score = scores[domain]
        triggered = (score < threshold) if domain in _LOW_SCORE_DOMAINS else (score > threshold)
        if triggered:
            if module not in suggested:
                suggested.append(module)
            insights.setdefault(ttype, {})[domain] = {
                "score": score, "suggested_module": module,
                "direction": "low" if domain in _LOW_SCORE_DOMAINS else "high",
            }

    # Crisis/severe stress: force duygusal_ruhsal + meditasyon_egzersiz
    stress_details = test_scores.get("stress_details", {})
    if isinstance(stress_details, dict):
        severity = stress_details.get("depression_severity", "")
        if severity in ("moderate", "moderately_severe", "severe"):
            for m in ("duygusal_ruhsal", "meditasyon_egzersiz"):
                if m not in suggested:
                    suggested.append(m)

    return suggested, insights


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
    lang_col = _LANG_COL_MAP.get(lang, lang)
    db   = get_backup()
    col  = db[f"coach_attributes_{lang_col}"]

    # Analiz sonucundan dominant sıfatları çıkar — 3 format desteklenir:
    # 1) attributes: [{name, score}]  — eski format
    # 2) top_sifatlar: [{sifat, score}] — enhanced_databases çıktısı
    # 3) sifat_scores: {name: float}  — enhanced_databases dict çıktısı
    _ar = body.analysis_result
    _arget = _ar.get
    attrs = _arget("attributes") or _arget("top_sifatlar", [])
    dominant_raw: list[str] = []
    if attrs:
        dominant_raw = [
            a.get("name") or a.get("sifat", "")
            for a in sorted(attrs, key=_KEY_SCORE, reverse=True)
            if a.get("name") or a.get("sifat")
        ][:5]
    else:
        ss = _arget("sifat_scores", {})
        if ss:
            dominant_raw = [k for k, _ in sorted(ss.items(), key=lambda x: -x[1])][:5]

    if not dominant_raw:
        raise HTTPException(400, "Analiz sonucunda sıfat bulunamadı (attributes/top_sifatlar/sifat_scores).")

    # Dual-lookup: her sıfat için önce PascalCase (Track B), yoksa archetype (Track A)
    valid_modules = [m for m in body.include_modules if m in COACH_MODULES]
    projection = {"_id": 1, **{m: 1 for m in valid_modules}}

    # Sıfat → DB key eşlemesi: Track B varsa direkt, yoksa archetype
    raw_keys    = [s for s in dominant_raw if s]
    pascal_hits = {
        doc["_id"]: doc
        for doc in col.find({"_id": {"$in": raw_keys}}, projection)
    }
    sifat_key_map: dict[str, str] = {}   # orijinal_sifat → DB _id
    archetype_lookups: list[str] = []
    for s in raw_keys:
        if s in pascal_hits:
            sifat_key_map[s] = s          # Track B direkt
        else:
            arch = _normalize_sifat(s)
            sifat_key_map[s] = arch
            archetype_lookups.append(arch)

    arch_docs = {
        doc["_id"]: doc
        for doc in col.find({"_id": {"$in": archetype_lookups}}, projection)
    } if archetype_lookups else {}
    sifat_docs = {**pascal_hits, **arch_docs}

    dominant = list(dict.fromkeys(sifat_key_map[s] for s in raw_keys))

    coach_output = {}
    for mod in valid_modules:
        mod_data = []
        for s in raw_keys:
            db_key = sifat_key_map[s]
            if db_key in sifat_docs and mod in sifat_docs[db_key]:
                mod_data.append({"sifat": s, "archetype": db_key, "data": sifat_docs[db_key][mod]})
        if mod_data:
            coach_output[mod] = mod_data

    # Psikolojik test skorlarından ek modül önerileri
    test_based_insights: dict = {}
    if body.test_scores:
        suggested_mods, test_based_insights = _test_scores_to_insights(body.test_scores)
        # Force-inject suggested modules that aren't already in coach_output
        for extra_mod in suggested_mods:
            if extra_mod not in coach_output and extra_mod in COACH_MODULES:
                extra_data = []
                for s in raw_keys:
                    db_key = sifat_key_map[s]
                    if db_key in sifat_docs and extra_mod in sifat_docs[db_key]:
                        extra_data.append({"sifat": s, "archetype": db_key, "data": sifat_docs[db_key][extra_mod]})
                if extra_data:
                    coach_output[extra_mod] = extra_data

    # Ek analiz verileri
    golden = _arget("golden_ratio", 0)
    face_type = _arget("face_type", "")

    # Uzun vadeli hafıza — body'den geldiyse kullan, yoksa DB'den çek
    user_id = get_user_id(authorization)
    memories: list = body.user_memories if body.user_memories is not None else []
    if not memories and user_id:
        memories = _fetch_user_memories(user_id)

    # Hafıza özetini modül önerilerine dahil et
    memory_insights: dict = {}
    if memories:
        goals    = [m["content"] for m in memories if m.get("category") == "goal"][:3]
        concerns = [m["content"] for m in memories if m.get("category") == "concern"][:2]
        prefs    = [m["content"] for m in memories if m.get("category") == "preference"][:3]
        if goals or concerns or prefs:
            memory_insights = {
                "goals":    goals,
                "concerns": concerns,
                "preferences": prefs,
            }

    has_health = bool(HEALTH_MODULES.intersection(coach_output.keys()))
    result = {
        "dominant_sifatlar":  dominant_raw,
        "archetypes_used":    dominant,
        "golden_ratio":       golden,
        "face_type":          face_type,
        "lang":               lang,
        "coach_modules":      coach_output,
        "generated_at":       datetime.now().isoformat(),
    }
    if test_based_insights:
        result["test_based_insights"] = test_based_insights
    if memory_insights:
        result["memory_insights"] = memory_insights
    if has_health:
        result["health_disclaimer"] = _get_disclaimer(lang)
    return result


# ── Endpoint: Tek sıfat + modül ───────────────────────────────────────────────
@app.get("/coach/sifat/{sifat}/{module}")
async def get_sifat_module(sifat: str, module: str, lang: str = "tr"):
    if not _RE_SIFAT.match(sifat):
        raise HTTPException(400, "Geçersiz sıfat formatı.")
    if module not in COACH_MODULES:
        raise HTTPException(400, f"Geçersiz modül. İzin verilenler: {', '.join(COACH_MODULES)}")
    if lang not in ALL_LANGS:
        lang = "tr"
    lang_col = _LANG_COL_MAP.get(lang, lang)
    db  = get_backup()
    col = db[f"coach_attributes_{lang_col}"]

    # Dual-lookup: Track B direkt kaydı önce, yoksa archetype proxy
    doc = col.find_one({"_id": sifat}, {module: 1, "_id": 0})
    if doc:
        resolved_key = sifat          # Track B direkt eşleşme
    else:
        resolved_key = _normalize_sifat(sifat)
        doc = col.find_one({"_id": resolved_key}, {module: 1, "_id": 0})
    if not doc:
        raise HTTPException(404, f"'{sifat}' → '{resolved_key}' bulunamadı.")
    if module not in doc:
        raise HTTPException(404, f"'{module}' modülü bu sıfat için mevcut değil.")
    response = {"sifat": sifat, "archetype": resolved_key, "module": module, "data": doc[module], "lang": lang}
    if module in HEALTH_MODULES:
        response["disclaimer"] = _get_disclaimer(lang)
    return response


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
    lang_col = _LANG_COL_MAP.get(lang, lang)
    db = get_backup()
    col = db[f"coach_attributes_{lang_col}"]

    # Dominant sıfatları çıkar (3 format: attributes / top_sifatlar / sifat_scores)
    _ar = body.analysis_result
    _arget = _ar.get
    attrs = _arget("attributes") or _arget("top_sifatlar", [])
    dominant_raw: list[str] = []
    if attrs:
        dominant_raw = [
            a.get("name") or a.get("sifat", "")
            for a in sorted(attrs, key=_KEY_SCORE, reverse=True)
            if a.get("name") or a.get("sifat")
        ][:body.top_n]
    else:
        ss = _arget("sifat_scores", {})
        if ss:
            dominant_raw = [k for k, _ in sorted(ss.items(), key=lambda x: -x[1])][:body.top_n]

    if not dominant_raw:
        # No sifatlar found — use generic fallback; giyim_base fallback below will handle it
        dominant_raw = ["karma-adaptif"]

    # Dual-lookup: Track B direkt, yoksa archetype
    pascal_docs = {doc["_id"]: doc for doc in col.find({"_id": {"$in": dominant_raw}, "giyim": {"$exists": True}}, {"giyim": 1})}
    arch_keys   = list(dict.fromkeys(_normalize_sifat(s) for s in dominant_raw if s not in pascal_docs))
    dominant    = ([s for s in dominant_raw if s in pascal_docs] + arch_keys) or arch_keys

    # Batch fetch giyim data for all dominant sifats (avoids N+1)
    giyim_base = None
    merged_docs = {**pascal_docs, **{doc["_id"]: doc for doc in col.find({"_id": {"$in": arch_keys}, "giyim": {"$exists": True}}, {"giyim": 1})}}
    for doc in (merged_docs[k] for k in dominant if k in merged_docs):
        if doc.get("giyim"):
            giyim_base = doc["giyim"]
            break

    if not giyim_base:
        # Fallback: karma-adaptif (default) şablonu — 4 mevsim × 4 kategori
        giyim_base = {
            "stil_tipi": "karma-adaptif",
            "coaching": {
                "felsefe": "Uyum ve pragmatizm. Giyim işlevsel, temiz ve herkes tarafından kabul edilebilir.",
                "kombinasyon": "Klasik kombinasyonlar hiçbir zaman başarısız olmaz. Beyaz tişört + koyu pantolon her zaman işe yarar.",
                "renk_psikolojisi": "Nötr renkler sakinlik ve profesyonellik verir. Siyah, beyaz, gri ve bej temel renk paketidir.",
                "yaşam_uyarlamasi": "Hızlı mix-and-match kombinasyonları tercih et. Az ama kaliteli parçalar gardrobunu basit tutar."
            },
            "renk_paleti": {"ana": ["#696969", "#808080", "#F5F5DC"], "vurgu": ["#000000", "#FFFFFF"], "kacin": []},
            "yuz_sekli_notu": {
                "oval": "Her kesim uygundur; V-yaka önerilir.",
                "kare": "Yumuşak yuvarlak yaka hatları dengeler.",
                "yuvarlak": "V-yaka ve dikey çizgiler yüzü uzatır.",
                "kalp": "Geniş omuz çizgileri alt yüzü dengeler.",
                "uzun": "Yatay çizgiler ve yüksek yaka dengeler.",
                "elmas": "Geniş yaka ve çan etek alt yapıyı dengeler.",
            },
            "mevsim": {
                "ilkbahar": {
                    "gunluk": {
                        "parca": ["beyaz tişört", "slim fit chino pantolon", "hafif trençkot", "beyaz spor ayakkabı"],
                        "kumas": ["pamuk", "keten blend"],
                        "kesim": "slim fit / relaxed",
                        "aksesuar": ["minimal saat", "küçük sırt çantası"],
                        "ipucu": "Pastel renkler ve açık tonlar ilkbaharın enerjisini yansıtır."
                    },
                    "spor": {
                        "parca": ["fermuarlı sweatshirt", "jogger eşofman altı", "hafif rüzgarlık", "koşu ayakkabısı"],
                        "kumas": ["pamuk blend", "polyester", "moisture-wicking"],
                        "kesim": "relaxed / tapered",
                        "aksesuar": ["spor çanta", "kep", "spor bilekliği"],
                        "ipucu": "Hafif katmanlama ilkbaharda ani hava değişikliklerine karşı korur."
                    },
                    "resmi": {
                        "parca": ["açık gri blazer", "beyaz gömlek", "koyu slim pantolon", "deri loafer"],
                        "kumas": ["hafif yün", "pamuk-elastan"],
                        "kesim": "slim / tailored",
                        "aksesuar": ["klasik kol saati", "deri kemer"],
                        "ipucu": "Blazer'ı günlük kombinlerle de kullanmak versatility sağlar."
                    },
                    "davet": {
                        "parca": ["lacivert blazer", "beyaz gömlek", "bej pantolon", "bağlı ayakkabı"],
                        "kumas": ["pamuk premium", "viskon blend"],
                        "kesim": "fitted",
                        "aksesuar": ["cep mendili", "şık saat", "ince kravat"],
                        "ipucu": "Blazer ve pantolonun farklı tonlarda olması modern smart-casual look yaratır."
                    },
                },
                "yaz": {
                    "gunluk": {
                        "parca": ["polo yaka tişört", "kısa chino şort", "espadrille veya sandalet"],
                        "kumas": ["hafif pamuk", "keten", "viskon"],
                        "kesim": "relaxed / loose",
                        "aksesuar": ["güneş gözlüğü", "hasır şapka", "kanvas çanta"],
                        "ipucu": "Açık renkler ısıyı yansıtır, nefes alan kumaşlar rahatlık sağlar."
                    },
                    "spor": {
                        "parca": ["kolsuz spor tişört", "spor şort", "hafif koşu ayakkabısı"],
                        "kumas": ["moisture-wicking", "mesh", "elastan"],
                        "kesim": "athletic / loose",
                        "aksesuar": ["spor güneş gözlüğü", "kep", "spor bilekliği"],
                        "ipucu": "UV koruyucu kumaşlar ve açık renkler yaz sporlarında idealdir."
                    },
                    "resmi": {
                        "parca": ["keten blazer", "açık renkli gömlek", "linen pantolon", "deri loafer"],
                        "kumas": ["keten", "hafif pamuk", "viskon"],
                        "kesim": "loose / tailored",
                        "aksesuar": ["hafif fular", "metal kol saati"],
                        "ipucu": "Keten kumaş yazın hem şık hem serin kalmanızı sağlar."
                    },
                    "davet": {
                        "parca": ["açık mavi gömlek", "beyaz chino pantolon", "espadrille veya loafer"],
                        "kumas": ["premium pamuk", "keten blend"],
                        "kesim": "slim / relaxed",
                        "aksesuar": ["güneş gözlüğü", "hasır aksesuar", "ince bileklik"],
                        "ipucu": "Yazlık davetlerde açık renkler ve doğal kumaşlar hem şık hem rahat hissettirir."
                    },
                },
                "sonbahar": {
                    "gunluk": {
                        "parca": ["kazak veya triko", "koyu slim jean", "bot veya sneaker", "kaban"],
                        "kumas": ["pamuk", "yün blend", "polar"],
                        "kesim": "slim / regular",
                        "aksesuar": ["bere", "deri çanta", "kashmere eşarp"],
                        "ipucu": "Toprak tonları (haki, kestane, hardal) sonbaharın renk paleti ile uyum sağlar."
                    },
                    "spor": {
                        "parca": ["uzun kollu sporcu tişörtü", "jogger pantolon", "rüzgarlık veya polar", "trail ayakkabısı"],
                        "kumas": ["fleece", "softshell", "technical nylon"],
                        "kesim": "tapered / athletic",
                        "aksesuar": ["spor bere", "spor çanta", "eldiven"],
                        "ipucu": "Katmanlı giyim sonbahar soğuklarına karşı en etkili çözümdür."
                    },
                    "resmi": {
                        "parca": ["koyu renk takım elbise", "beyaz veya mavi gömlek", "kravat", "deri ayakkabı"],
                        "kumas": ["yün", "yün-polyester blend"],
                        "kesim": "slim / classic fit",
                        "aksesuar": ["kol düğmesi", "deri kemer", "klasik saat"],
                        "ipucu": "Koyu renk takımlar sonbaharda hem güçlü hem şık görünüm sağlar."
                    },
                    "davet": {
                        "parca": ["koyu navy blazer", "gri pantolon", "gömlek", "deri oxford ayakkabı"],
                        "kumas": ["yün blend", "premium pamuk"],
                        "kesim": "tailored",
                        "aksesuar": ["şık saat", "cep mendili", "ince eşarp"],
                        "ipucu": "Navy ve gri kombinasyonu sonbahar davetlerinde her zaman güvenli ve şık bir seçimdir."
                    },
                },
                "kis": {
                    "gunluk": {
                        "parca": ["kalın kazak", "koyu slim jean", "kışlık bot", "uzun palto veya kaban"],
                        "kumas": ["yün", "kaşmir blend", "polar", "denim"],
                        "kesim": "regular / relaxed",
                        "aksesuar": ["bere", "kaşmir eşarp", "deri eldivenler"],
                        "ipucu": "Katmanlı giyim ve kaliteli dış giysi kışın hem sıcak hem şık kalmanızı sağlar."
                    },
                    "spor": {
                        "parca": ["termal iç çamaşır", "polar eşofman", "rüzgarlık veya mont", "yüksek bilekli spor ayakkabı"],
                        "kumas": ["termal", "fleece", "windproof"],
                        "kesim": "athletic / tapered",
                        "aksesuar": ["ısıtıcı bere", "eldiven", "boyunluk"],
                        "ipucu": "Termal iç katman soğukta vücut ısısını korurken hareket özgürlüğü sağlar."
                    },
                    "resmi": {
                        "parca": ["koyu yün palto", "takım elbise", "gömlek + kravat", "deri çizme veya ayakkabı"],
                        "kumas": ["yün", "kaşmir", "merinos"],
                        "kesim": "classic / slim fit",
                        "aksesuar": ["deri eldiven", "kaşmir eşarp", "klasik şapka veya bere"],
                        "ipucu": "Uzun yün palto kışın en şık dış giysi seçeneğidir, takımın üzerine mükemmel durur."
                    },
                    "davet": {
                        "parca": ["koyu kadife blazer veya takım", "beyaz gömlek", "koyu pantolon", "şık çizme veya ayakkabı"],
                        "kumas": ["kadife", "yün blend", "premium viskon"],
                        "kesim": "fitted / tailored",
                        "aksesuar": ["şık saat", "cep mendili", "ince kaşmir eşarp"],
                        "ipucu": "Kadife ve koyu renkler kış davetlerinde sofistike ve göz alıcı bir görünüm yaratır."
                    },
                },
            }
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
    astro    = _calculate_basic_astrology(_bd, _bbt, lang, body.birth_city)
    numerology = _calculate_numerology(_bd, lang)

    result: dict = {
        "birth_date":  _bd,
        "birth_time":  _bbt,
        "astrology":   astro,
        "numerology":  numerology,
        "lang":        lang,
    }
    if body.name:
        result["name_numerology"] = _calculate_name_numerology(body.name, lang)

    # Yüz × Doğum örtüşme analizi — giriş yapmış kullanıcılar için
    if user_id:
        try:
            _bd_dt = datetime.strptime(_bd[:10], "%Y-%m-%d")
            _sign_idx = _get_sign_idx(_bd_dt.month, _bd_dt.day)
            _en_sign  = _ZODIAC_NAMES['en'][_sign_idx]   # 'Aries', 'Leo', …
            _tr_sign  = astro.get("sun_sign", _en_sign)  # zaten dile çevrilmiş
        except Exception:
            _en_sign = _tr_sign = ""
        face_sifatlar = _get_user_face_sifatlar(user_id)
        result["face_astro_match"] = _build_face_astro_match(_en_sign, _tr_sign, face_sifatlar, lang)

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
    "tr": "Yükselen burcu hesaplamak için doğum saati ve şehri girin",
    "en": "Enter birth time and city to calculate rising sign",
    "de": "Geben Sie Geburtszeit und -ort an, um den Aszendenten zu berechnen",
    "ru": "Введите время и город рождения для расчёта асцендента",
    "ar": "أدخل وقت الميلاد والمدينة لحساب الطالع",
    "es": "Ingresa hora y ciudad de nacimiento para calcular el ascendente",
    "ko": "상승 별자리를 계산하려면 출생 시간과 도시를 입력하세요",
    "ja": "上昇点を計算するには出生時刻と都市を入力してください",
    "zh": "输入出生时间和城市以计算上升星座",
    "hi": "उदय राशि की गणना के लिए जन्म समय और शहर दर्ज करें",
    "fr": "Entrez l'heure et la ville de naissance pour calculer l'ascendant",
    "pt": "Insira hora e cidade de nascimento para calcular o ascendente",
    "bn": "উদয় রাশি গণনার জন্য জন্মের সময় ও শহর দিন",
    "id": "Masukkan waktu dan kota kelahiran untuk menghitung tanda rising",
    "ur": "طلوع نشان کا حساب لگانے کے لیے پیدائش کا وقت اور شہر درج کریں",
    "it": "Inserisci ora e città di nascita per calcolare l'ascendente",
    "vi": "Nhập giờ sinh và thành phố để tính cung mọc",
    "pl": "Podaj godzinę i miasto urodzenia, aby obliczyć znak wznoszący",
}

_ASTRO_CITY_NOT_FOUND = {
    "tr": "Şehir bulunamadı — lütfen İngilizce şehir adı deneyin (ör. Istanbul, Paris)",
    "en": "City not found — try English city name (e.g. Istanbul, Paris)",
    "de": "Stadt nicht gefunden — englischen Namen versuchen (z.B. Istanbul, Paris)",
    "ru": "Город не найден — попробуйте английское название (напр. Istanbul, Paris)",
    "ar": "لم يتم العثور على المدينة — جرّب الاسم بالإنجليزية",
    "es": "Ciudad no encontrada — intenta con el nombre en inglés (ej. Istanbul, Paris)",
    "ko": "도시를 찾을 수 없습니다 — 영어 도시 이름으로 시도해보세요",
    "ja": "都市が見つかりません — 英語の都市名で試してください",
    "zh": "未找到城市 — 请尝试英文城市名（如 Istanbul, Paris）",
    "hi": "शहर नहीं मिला — अंग्रेज़ी शहर का नाम आज़माएं",
    "fr": "Ville introuvable — essayez le nom anglais (ex. Istanbul, Paris)",
    "pt": "Cidade não encontrada — tente o nome em inglês (ex. Istanbul, Paris)",
    "bn": "শহর পাওয়া যায়নি — ইংরেজিতে শহরের নাম দিন",
    "id": "Kota tidak ditemukan — coba nama kota dalam bahasa Inggris",
    "ur": "شہر نہیں ملا — انگریزی نام آزمائیں (مثلاً Istanbul, Paris)",
    "it": "Città non trovata — prova il nome in inglese (es. Istanbul, Paris)",
    "vi": "Không tìm thấy thành phố — thử tên tiếng Anh (vd. Istanbul, Paris)",
    "pl": "Miasto nie znalezione — spróbuj angielskiej nazwy (np. Istanbul, Paris)",
}

# Kerykeion → nindex eşleştirmesi (_ZODIAC_NAMES ile aynı sıra)
_KERYKEION_SIGN_MAP = {
    "Aquarius": 0, "Pisces": 1, "Aries": 2, "Taurus": 3,
    "Gemini": 4, "Cancer": 5, "Leo": 6, "Virgo": 7,
    "Libra": 8, "Scorpio": 9, "Sagittarius": 10, "Capricorn": 11,
}


def _calculate_rising_sign(
    birth_date_str: str,
    birth_time_str: str,
    birth_city: str,
    lang: str = "en",
) -> dict:
    """
    Kerykeion (Swiss Ephemeris) ile yükselen burcu hesapla.
    Geocoding: Nominatim (OpenStreetMap, ücretsiz) → lat/lng
    Timezone : timezonefinder → tz_str
    Kerykeion: online=False, lat/lng/tz_str direkt verilir (GeoNames yok)
    """
    if not _KERYKEION_OK:
        return {"error": "kerykeion not installed"}

    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d")
        bt = datetime.strptime(birth_time_str, "%H:%M")

        # 1 — Şehri koordinata çevir
        location = _GEO.geocode(birth_city, timeout=8)
        if location is None:
            return {"error": _ASTRO_CITY_NOT_FOUND.get(lang, _ASTRO_CITY_NOT_FOUND["en"])}

        lat = location.latitude
        lng = location.longitude
        city_resolved = location.address.split(",")[0].strip()

        # 2 — Koordinattan timezone bul
        tz_str = _TF.timezone_at(lat=lat, lng=lng) or "UTC"

        # 3 — Yükselen burcu hesapla (online=False → GeoNames çağrısı yok)
        subject = AstrologicalSubject(
            "user",
            bd.year, bd.month, bd.day,
            bt.hour, bt.minute,
            city=city_resolved,
            lat=lat,
            lng=lng,
            tz_str=tz_str,
            online=False,
        )

        sign_en  = subject.first_house.sign
        sign_idx = _KERYKEION_SIGN_MAP.get(sign_en)
        if sign_idx is None:
            return {"error": f"Unknown sign: {sign_en}"}

        zodiac     = _ZODIAC_NAMES.get(lang, _ZODIAC_NAMES["en"])
        sign_local = zodiac[sign_idx]

        return {
            "rising_sign":    sign_local,
            "rising_sign_en": sign_en,
            "rising_degree":  round(float(subject.first_house.position), 1),
            "city_resolved":  city_resolved,
            "lat":            round(lat, 4),
            "lng":            round(lng, 4),
        }

    except Exception as exc:
        log.warning("Rising sign calc error for '%s': %s", birth_city, exc)
        return {"error": _ASTRO_CITY_NOT_FOUND.get(lang, _ASTRO_CITY_NOT_FOUND["en"])}
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

@lru_cache(maxsize=256)
def _get_sign_idx(month: int, day: int) -> int:
    """Return zodiac sign index (0–11) for a given birth month and day."""
    signs_dates = [
        ((1,20),(2,18),0),   ((2,19),(3,20),1),   ((3,21),(4,19),2),   ((4,20),(5,20),3),
        ((5,21),(6,20),4),   ((6,21),(7,22),5),   ((7,23),(8,22),6),   ((8,23),(9,22),7),
        ((9,23),(10,22),8),  ((10,23),(11,21),9), ((11,22),(12,21),10),((12,22),(1,19),11),
    ]
    for (sm,sd),(em,ed),idx in signs_dates:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return idx
    return 11  # Default Capricorn


def _calculate_basic_astrology(birth_date_str: str, birth_time_str: Optional[str] = None, lang: str = "tr", birth_city: Optional[str] = None) -> dict:
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
    sign_idx = _get_sign_idx(_bdm, _bdd)
    sun_sign = _get_sun_sign(_bdm, _bdd, lang)
    element  = _get_element(sign_idx, lang)
    quality  = _get_quality(sign_idx, lang)

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
            result["birth_hour"]  = _bth
            result["time_energy"] = _get_time_energy(_bth, lang)

            if birth_city and birth_city.strip():
                # Gerçek yükselen burç hesabı
                rising = _calculate_rising_sign(birth_date_str, birth_time_str, birth_city.strip(), lang)
                if "error" in rising:
                    result["rising_hint"]  = rising["error"]
                else:
                    result["rising_sign"]   = rising["rising_sign"]
                    result["rising_sign_en"]= rising["rising_sign_en"]
                    result["rising_degree"] = rising["rising_degree"]
                    result["city_resolved"] = rising["city_resolved"]
                    result["lat"]           = rising["lat"]
                    result["lng"]           = rising["lng"]
            else:
                result["rising_hint"] = _ASTRO_RISING_HINT.get(lang, _ASTRO_RISING_HINT["en"])

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


_MASTER_NUMBERS = {
    "tr": {11: "Usta Sayı — Yüksek Sezgi", 22: "Usta Sayı — Büyük Mimar", 33: "Usta Sayı — Evrensel Şifacı"},
    "en": {11: "Master Number — High Intuition", 22: "Master Number — Great Architect", 33: "Master Number — Universal Healer"},
    "de": {11: "Meisterzahl — Hohe Intuition", 22: "Meisterzahl — Großer Architekt", 33: "Meisterzahl — Universeller Heiler"},
    "ru": {11: "Мастер-число — Высокая интуиция", 22: "Мастер-число — Великий архитектор", 33: "Мастер-число — Универсальный целитель"},
    "ar": {11: "رقم رئيسي — حدس عالٍ", 22: "رقم رئيسي — المعماري العظيم", 33: "رقم رئيسي — المعالج الكوني"},
    "es": {11: "Número maestro — Alta intuición", 22: "Número maestro — Gran arquitecto", 33: "Número maestro — Sanador universal"},
    "ko": {11: "마스터 넘버 — 높은 직관", 22: "마스터 넘버 — 위대한 건축가", 33: "마스터 넘버 — 우주적 치유자"},
    "ja": {11: "マスターナンバー — 高い直感", 22: "マスターナンバー — 偉大な建築家", 33: "マスターナンバー — 宇宙のヒーラー"},
    "zh": {11: "主数 — 高度直觉", 22: "主数 — 伟大建筑师", 33: "主数 — 宇宙治愈者"},
    "hi": {11: "मास्टर नंबर — उच्च अंतर्ज्ञान", 22: "मास्टर नंबर — महान वास्तुकार", 33: "मास्टर नंबर — सार्वभौमिक उपचारक"},
    "fr": {11: "Nombre maître — Haute intuition", 22: "Nombre maître — Grand architecte", 33: "Nombre maître — Guérisseur universel"},
    "pt": {11: "Número mestre — Alta intuição", 22: "Número mestre — Grande arquiteto", 33: "Número mestre — Curador universal"},
    "bn": {11: "মাস্টার সংখ্যা — উচ্চ অন্তর্দৃষ্টি", 22: "মাস্টার সংখ্যা — মহান স্থপতি", 33: "মাস্টার সংখ্যা — সার্বজনীন নিরাময়কারী"},
    "id": {11: "Angka master — Intuisi tinggi", 22: "Angka master — Arsitek agung", 33: "Angka master — Penyembuh universal"},
    "ur": {11: "ماسٹر نمبر — اعلی وجدان", 22: "ماسٹر نمبر — عظیم معمار", 33: "ماسٹر نمبر — آفاقی شفاء دینے والا"},
    "it": {11: "Numero maestro — Alta intuizione", 22: "Numero maestro — Grande architetto", 33: "Numero maestro — Guaritore universale"},
    "vi": {11: "Số chủ — Trực giác cao", 22: "Số chủ — Kiến trúc sư vĩ đại", 33: "Số chủ — Người chữa bệnh vũ trụ"},
    "pl": {11: "Liczba mistrzowska — Wysoka intuicja", 22: "Liczba mistrzowska — Wielki architekt", 33: "Liczba mistrzowska — Uzdrowiciel uniwersalny"},
}

_PERSONAL_YEAR_LABELS = {
    "tr": "Kişisel Yıl Sayısı",
    "en": "Personal Year Number",
    "de": "Persönliche Jahreszahl",
    "ru": "Личный год",
    "ar": "رقم السنة الشخصية",
    "es": "Número de Año Personal",
    "ko": "개인 연도 번호",
    "ja": "パーソナルイヤーナンバー",
    "zh": "个人年数",
    "hi": "व्यक्तिगत वर्ष संख्या",
    "fr": "Nombre de l'Année Personnelle",
    "pt": "Número do Ano Pessoal",
    "bn": "ব্যক্তিগত বছর সংখ্যা",
    "id": "Angka Tahun Pribadi",
    "ur": "ذاتی سال نمبر",
    "it": "Numero dell'Anno Personale",
    "vi": "Số Năm Cá Nhân",
    "pl": "Liczba Roku Osobistego",
}


def _calculate_numerology(birth_date_str: str, lang: str = "tr") -> dict:
    """Numerology calculation — life path, personal year, master number flag."""
    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d")
    except ValueError:
        return {}

    def reduce(n: int) -> int:
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    def reduce_no_master(n: int) -> int:
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n

    day   = reduce(bd.day)
    month = reduce(bd.month)
    year  = reduce(sum(int(d) for d in str(bd.year)))
    life  = reduce(day + month + year)

    current_year = datetime.now().year
    cur_year_digits = reduce_no_master(sum(int(d) for d in str(current_year)))
    personal_year = reduce_no_master(bd.day + bd.month + cur_year_digits)
    if personal_year == 0:
        personal_year = 9

    meaning_dict = _NUMEROLOGY_MEANINGS.get(lang, _NUMEROLOGY_MEANINGS["en"])
    master_dict  = _MASTER_NUMBERS.get(lang, _MASTER_NUMBERS["en"])

    result = {
        "life_path_number":    life,
        "life_path_meaning":   meaning_dict.get(life, ""),
        "day_number":          day,
        "month_number":        month,
        "year_number":         year,
        "personal_year_number": personal_year,
        "personal_year_meaning": meaning_dict.get(personal_year, ""),
        "personal_year_label": _PERSONAL_YEAR_LABELS.get(lang, _PERSONAL_YEAR_LABELS["en"]),
        "current_year":        current_year,
        "is_master_number":    life in (11, 22, 33),
    }
    if life in (11, 22, 33):
        result["master_label"] = master_dict.get(life, "")
    return result


# Pythagorean letter → number mapping (ASCII + Turkish chars)
_PYTHAGOREAN: dict[str, int] = {
    'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
    'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
    's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8,
    # Turkish extras
    'ç':3,'ğ':7,'ı':9,'İ':9,'ö':6,'ş':1,'ü':3,
}
_VOWELS = set('aeıioöuüAEIİOÖUÜ')

_NAME_LABELS = {
    "tr": {"title":"İsim Analizi","expression":"İfade Sayısı","soul_urge":"Ruh İtkisi","personality":"Kişilik Sayısı","ebced_title":"Ebced Analizi","kabala_title":"Kabala Analizi","total":"Toplam","reduced":"Sayısal Değer"},
    "en": {"title":"Name Analysis","expression":"Expression Number","soul_urge":"Soul Urge","personality":"Personality Number","ebced_title":"Abjad Analysis","kabala_title":"Kabbalah Analysis","total":"Total","reduced":"Reduced Number"},
    "de": {"title":"Namensanalyse","expression":"Ausdruckszahl","soul_urge":"Seelenimpuls","personality":"Persönlichkeitszahl","ebced_title":"Abjad-Analyse","kabala_title":"Kabbala-Analyse","total":"Gesamt","reduced":"Reduzierte Zahl"},
    "ru": {"title":"Анализ имени","expression":"Число выражения","soul_urge":"Число душевного стремления","personality":"Число личности","ebced_title":"Абджад-анализ","kabala_title":"Каббала-анализ","total":"Сумма","reduced":"Сведённое число"},
    "ar": {"title":"تحليل الاسم","expression":"رقم التعبير","soul_urge":"رقم النفس","personality":"رقم الشخصية","ebced_title":"تحليل الأبجد","kabala_title":"تحليل القبالاه","total":"المجموع","reduced":"العدد المختزل"},
    "es": {"title":"Análisis de Nombre","expression":"Número de Expresión","soul_urge":"Impulso del Alma","personality":"Número de Personalidad","ebced_title":"Análisis Abyad","kabala_title":"Análisis Cabalístico","total":"Total","reduced":"Número Reducido"},
    "ko": {"title":"이름 분석","expression":"표현 숫자","soul_urge":"영혼 충동","personality":"성격 숫자","ebced_title":"아브자드 분석","kabala_title":"카발라 분석","total":"합계","reduced":"환원 숫자"},
    "ja": {"title":"名前の分析","expression":"表現数","soul_urge":"魂の衝動","personality":"個性数","ebced_title":"アブジャド分析","kabala_title":"カバラ分析","total":"合計","reduced":"縮約数"},
    "zh": {"title":"姓名分析","expression":"表达数","soul_urge":"灵魂冲动","personality":"个性数","ebced_title":"阿布贾德分析","kabala_title":"卡巴拉分析","total":"总计","reduced":"归约数"},
    "hi": {"title":"नाम विश्लेषण","expression":"अभिव्यक्ति संख्या","soul_urge":"आत्मा आवेग","personality":"व्यक्तित्व संख्या","ebced_title":"अब्जद विश्लेषण","kabala_title":"कबाला विश्लेषण","total":"कुल","reduced":"न्यूनीकृत संख्या"},
    "fr": {"title":"Analyse du Prénom","expression":"Nombre d'Expression","soul_urge":"Élan de l'Âme","personality":"Nombre de Personnalité","ebced_title":"Analyse Abjad","kabala_title":"Analyse Kabbalistique","total":"Total","reduced":"Nombre Réduit"},
    "pt": {"title":"Análise do Nome","expression":"Número de Expressão","soul_urge":"Impulso da Alma","personality":"Número de Personalidade","ebced_title":"Análise Abjad","kabala_title":"Análise Cabalística","total":"Total","reduced":"Número Reduzido"},
    "bn": {"title":"নাম বিশ্লেষণ","expression":"প্রকাশ সংখ্যা","soul_urge":"আত্মার আকাঙ্ক্ষা","personality":"ব্যক্তিত্ব সংখ্যা","ebced_title":"আবজাদ বিশ্লেষণ","kabala_title":"কাবালা বিশ্লেষণ","total":"মোট","reduced":"হ্রাসকৃত সংখ্যা"},
    "id": {"title":"Analisis Nama","expression":"Angka Ekspresi","soul_urge":"Dorongan Jiwa","personality":"Angka Kepribadian","ebced_title":"Analisis Abjad","kabala_title":"Analisis Kabbalah","total":"Total","reduced":"Angka Reduksi"},
    "ur": {"title":"نام کا تجزیہ","expression":"اظہار نمبر","soul_urge":"روحانی خواہش","personality":"شخصیت نمبر","ebced_title":"ابجد تجزیہ","kabala_title":"کبالہ تجزیہ","total":"کل","reduced":"تخفیفی عدد"},
    "it": {"title":"Analisi del Nome","expression":"Numero di Espressione","soul_urge":"Impulso dell'Anima","personality":"Numero di Personalità","ebced_title":"Analisi Abjad","kabala_title":"Analisi Kabbalistica","total":"Totale","reduced":"Numero Ridotto"},
    "vi": {"title":"Phân Tích Tên","expression":"Số Biểu Đạt","soul_urge":"Số Ham Muốn Tâm Hồn","personality":"Số Nhân Cách","ebced_title":"Phân Tích Abjad","kabala_title":"Phân Tích Kabbalah","total":"Tổng","reduced":"Số Rút Gọn"},
    "pl": {"title":"Analiza Imienia","expression":"Liczba Ekspresji","soul_urge":"Impuls Duszy","personality":"Liczba Osobowości","ebced_title":"Analiza Abjad","kabala_title":"Analiza Kabalistyczna","total":"Suma","reduced":"Liczba Zredukowana"},
}

# Ebced (Arabic Abjad) — traditional Islamic letter-number values mapped to Latin/Turkish
_EBCED_MAP: dict[str, int] = {
    'a':1,   'b':2,   'c':3,   'ç':3,   'd':4,   'e':5,   'f':80,
    'g':3,   'ğ':1000,'h':8,   'ı':10,  'i':10,  'j':3,   'k':20,
    'l':30,  'm':40,  'n':50,  'o':70,  'ö':70,  'p':80,  'q':100,
    'r':200, 's':60,  'ş':300, 't':400, 'u':6,   'ü':6,   'v':6,
    'w':6,   'x':60,  'y':10,  'z':7,
}

# Kabala (Hebrew Gematria — Mispar Hechrachi) mapped to Latin/Turkish letters
_KABALA_MAP: dict[str, int] = {
    'a':1,   'b':2,   'c':20,  'ç':3,   'd':4,   'e':5,   'f':80,
    'g':3,   'ğ':3,   'h':8,   'ı':10,  'i':10,  'j':3,   'k':20,
    'l':30,  'm':40,  'n':50,  'o':70,  'ö':70,  'p':80,  'q':100,
    'r':200, 's':300, 'ş':300, 't':400, 'u':6,   'ü':6,   'v':6,
    'w':6,   'x':60,  'y':10,  'z':7,
}


def _calculate_name_numerology(name: str, lang: str = "tr") -> dict:
    """Pythagorean + Ebced + Kabala name numerology."""
    clean = name.strip()
    if not clean:
        return {}

    def reduce_master(n: int) -> int:
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    def reduce_simple(n: int) -> int:
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n or 9

    low = clean.lower()

    # — Pythagorean —
    letters    = [ch for ch in low if ch in _PYTHAGOREAN]
    vowels     = [ch for ch in low if ch in _VOWELS and ch in _PYTHAGOREAN]
    consonants = [ch for ch in low if ch in _PYTHAGOREAN and ch not in _VOWELS]

    if not letters:
        return {}

    expression  = reduce_master(sum(_PYTHAGOREAN[ch] for ch in letters))
    soul_urge   = reduce_master(sum(_PYTHAGOREAN[ch] for ch in vowels))   if vowels   else 0
    personality = reduce_master(sum(_PYTHAGOREAN[ch] for ch in consonants)) if consonants else 0

    # — Ebced (Arabic Abjad) —
    ebced_letters = [ch for ch in low if ch in _EBCED_MAP]
    ebced_total   = sum(_EBCED_MAP[ch] for ch in ebced_letters)
    ebced_reduced = reduce_simple(ebced_total)

    # — Kabala (Hebrew Gematria) —
    kab_letters   = [ch for ch in low if ch in _KABALA_MAP]
    kabala_total  = sum(_KABALA_MAP[ch] for ch in kab_letters)
    kabala_reduced = reduce_simple(kabala_total)

    meaning_dict = _NUMEROLOGY_MEANINGS.get(lang, _NUMEROLOGY_MEANINGS["en"])
    labels = _NAME_LABELS.get(lang, _NAME_LABELS["en"])

    return {
        "name":               clean,
        "expression_number":  expression,
        "expression_meaning": meaning_dict.get(expression, ""),
        "soul_urge_number":   soul_urge,
        "soul_urge_meaning":  meaning_dict.get(soul_urge, ""),
        "personality_number": personality,
        "personality_meaning":meaning_dict.get(personality, ""),
        "ebced": {
            "total":   ebced_total,
            "reduced": ebced_reduced,
            "meaning": meaning_dict.get(ebced_reduced, ""),
        },
        "kabala": {
            "total":   kabala_total,
            "reduced": kabala_reduced,
            "meaning": meaning_dict.get(kabala_reduced, ""),
        },
        "labels": labels,
    }
