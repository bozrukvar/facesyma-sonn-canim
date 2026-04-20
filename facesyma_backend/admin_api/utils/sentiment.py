"""
admin_api/utils/sentiment.py
=============================
Keyword tabanlı duygu analizi (Türkçe + İngilizce).
Harici kütüphane gerektirmez.
"""

import re
import unicodedata

# ──── TÜRKÇE KEYWORDLER ─────────────────────────────────────────────────────
TR_POSITIVE = [
    "harika", "mükemmel", "süper", "sevdim", "çok iyi", "güzel", "beğendim",
    "başarılı", "muhteşem", "enfes", "kübra", "efsane", "iyiydi", "iyiyim",
    "mutluyum", "sevinç", "teşekkür", "minnettar", "takdir", "tebrik",
    "iyi", "güvenli", "hızlı", "kolay", "kullanışlı", "pratik", "yararlı",
    "faydalı", "iyi yapılmış", "profesyonel", "istikrarlı", "kararlı",
    "memnun", "tatmin", "gıpta", "aziz", "nitelikli", "yüksek kalite",
    "harikalar", "fantastik", "inanılmaz", "büyüleyici", "çekici", "akıllı"
]

TR_NEGATIVE = [
    "kötü", "berbat", "beğenmedim", "çalışmıyor", "bozuk", "yavaş", "hata",
    "sorun", "kötüydü", "hayal kırıklığı", "üzgün", "sinirli", "kızgın",
    "rahatsız", "mutsuz", "pişman", "memnun değil", "başarısız", "zayıf",
    "güvenli değil", "karmaşık", "zor", "sıkıcı", "monoton", "kırıcı",
    "acı", "ağır", "düşük kalite", "berbat", "feci", "korkunç", "felaket",
    "çöp", "saçma", "aptal", "garip", "alışılmadık", "hatalı", "yanlış",
    "eksik", "tamamlanmamış", "daha iyi olabilir", "hayal kırıcı"
]

# ──── İNGİLİZCE KEYWORDLER ──────────────────────────────────────────────────
EN_POSITIVE = [
    "great", "excellent", "amazing", "love", "perfect", "wonderful", "good",
    "fantastic", "awesome", "brilliant", "superb", "outstanding", "beautiful",
    "happy", "satisfied", "pleased", "impressed", "impressive", "superior",
    "best", "nice", "cool", "easy", "simple", "fast", "quick", "reliable",
    "secure", "stable", "useful", "helpful", "practical", "effective",
    "quality", "professional", "smart", "intelligent", "clever", "well",
    "glorious", "splendid", "remarkable", "noteworthy", "excellent work"
]

EN_NEGATIVE = [
    "bad", "terrible", "awful", "horrible", "hate", "poor", "worse", "worst",
    "broken", "doesn't work", "crash", "error", "bug", "issue", "problem",
    "slow", "difficult", "hard", "confusing", "complicated", "messy",
    "sad", "disappointed", "frustrated", "angry", "upset", "annoyed",
    "insecure", "unstable", "unsafe", "unreliable", "useless", "useless",
    "low quality", "amateur", "weak", "garbage", "trash", "waste", "rubbish",
    "pathetic", "pitiful", "despicable", "worst ever", "never again",
    "not working", "doesn't do", "incomplete", "unfinished", "buggy"
]

# ──── KONTROL AMAÇLI KEYWORDLER (Nötr eğilim tespit için) ────────────────────
NEUTRAL_INDICATORS = [
    "tamam", "idare eder", "ortalama", "normal", "standart", "fena değil",
    "okay", "alright", "average", "normal", "decent", "not bad", "so-so"
]


def _normalize_text(text: str) -> str:
    """
    Metni normalize et: küçük harfe, noktalama kaldır, Türkçe karakterleri düzelt.
    """
    # Küçük harfe dönüştür
    text = text.lower()

    # Türkçe karakterleri normalize et
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Noktalama ve özel karakterleri kaldır (boşluk bırak)
    text = re.sub(r'[^\w\s]', ' ', text)

    # Çoklu boşlukları tek boşluğa dönüştür
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def analyze_sentiment(text: str) -> dict:
    """
    Metinde duygu analizi yap (positive, neutral, negative).

    Args:
        text: Analiz edilecek metin

    Returns:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "score": float (-1.0 to 1.0),
            "pos_hits": int,
            "neg_hits": int,
            "confidence": float (0.0 to 1.0)
        }
    """
    if not text or not isinstance(text, str):
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "pos_hits": 0,
            "neg_hits": 0,
            "confidence": 0.0
        }

    normalized = _normalize_text(text)
    words = normalized.split()

    # Keyword sayıları
    pos_hits = sum(1 for word in words if word in TR_POSITIVE or word in EN_POSITIVE)
    neg_hits = sum(1 for word in words if word in TR_NEGATIVE or word in EN_NEGATIVE)
    neu_hits = sum(1 for word in words if word in NEUTRAL_INDICATORS)

    total_hits = pos_hits + neg_hits + neu_hits

    # Skor hesapla: -1.0 (most negative) to 1.0 (most positive)
    if total_hits == 0:
        score = 0.0
        confidence = 0.0
    else:
        score = (pos_hits - neg_hits) / total_hits
        confidence = min(total_hits / 10, 1.0)  # En fazla 10 hit için %100 güven

    # Sentiment belirle
    if score > 0.2:
        sentiment = "positive"
    elif score < -0.2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": round(score, 2),
        "pos_hits": pos_hits,
        "neg_hits": neg_hits,
        "confidence": round(confidence, 2)
    }
