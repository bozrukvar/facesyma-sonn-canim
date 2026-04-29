"""
generate_coach_sifatlar.py
===========================
21 sıfatı Coach DB'ye ekler — 13 modül + giyim + astroloji/doğum.

Akış:
  FAZ 1: Her sıfat için tüm modüller İngilizce Groq ile üretilir.
  FAZ 2: Türkçe — title/description native Groq, geri kalan Google Translate.
  FAZ 3: Diğer 16 dil — tamamı Google Translate (deep_translator).

Çalıştırma (ai_chat container içinde):
  pip install deep-translator
  python /tmp/generate_coach_sifatlar.py

İlerleme dosyası: /tmp/coach_gen_progress.json — kesintide devam sağlar.

RAG Notu:
  Tip B dict modüllerin her öğesinde "neden" alanı bulunur.
  Bu alan, önerinin NEDEN bu sıfata uygun olduğunu açıklar.
  Gelecekteki vector embedding / RAG aramaları için kritik semantik bağlantıdır.
"""

import os, json, time, re, sys
from datetime import datetime, timezone
from pymongo import MongoClient
from groq import Groq

try:
    from deep_translator import GoogleTranslator
    _GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    _GOOGLE_TRANSLATE_AVAILABLE = False
    print("UYARI: deep-translator yüklü değil. `pip install deep-translator` çalıştırın.")

# ── Config ─────────────────────────────────────────────────────────────────────
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
MONGO_URI     = os.environ.get("MONGO_URI", "")
MODEL_SMART   = "llama-3.3-70b-versatile"
MODEL_FAST    = "llama-3.1-8b-instant"
PROGRESS_FILE = "/tmp/coach_gen_progress.json"
REQUEST_DELAY = 2.5
BATCH_SIZE    = 3
BATCH_DELAY   = 4.0

groq_client  = Groq(api_key=GROQ_API_KEY)
MODEL        = MODEL_SMART
mongo_client = MongoClient(MONGO_URI)
DB           = mongo_client["facesyma-coach-backup"]

# ── 21 sıfat ──────────────────────────────────────────────────────────────────
SIFATLAR = {
    "kararlı":      "determined",
    "güvenilir":    "reliable",
    "dengeli":      "balanced",
    "güçlü":        "strong",
    "lider":        "leader",
    "enerjik":      "energetic",
    "zarif":        "elegant",
    "narin":        "delicate",
    "sanatsal":     "artistic",
    "yaratıcı":     "creative",
    "hassas":       "sensitive",
    "çekici":       "attractive",
    "uyumlu":       "adaptable",
    "sosyal":       "social",
    "cazip":        "charming",
    "pratik":       "practical",
    "dikkatli":     "careful",
    "analitik":     "analytical",
    "odaklı":       "focused",
    "sezgisel":     "intuitive",
    "açık_kalpli":  "open-hearted",
}

# ── Dil haritası ───────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": ("en",  "English",    "English"),
    "tr": ("tr",  "Turkish",    "Turkish"),
    "ar": ("ar",  "Arabic",     "Arabic"),
    "de": ("de",  "German",     "German"),
    "ja": ("jp",  "Japanese",   "Japanese"),
    "ko": ("kr",  "Korean",     "Korean"),
    "ru": ("ru",  "Russian",    "Russian"),
    "es": ("sp",  "Spanish",    "Spanish"),
    "bn": ("bn",  "Bengali",    "Bengali"),
    "fr": ("fr",  "French",     "French"),
    "hi": ("hi",  "Hindi",      "Hindi"),
    "id": ("id",  "Indonesian", "Indonesian"),
    "it": ("it",  "Italian",    "Italian"),
    "pl": ("pl",  "Polish",     "Polish"),
    "pt": ("pt",  "Portuguese", "Portuguese"),
    "ur": ("ur",  "Urdu",       "Urdu"),
    "vi": ("vi",  "Vietnamese", "Vietnamese"),
    "zh": ("zh",  "Chinese",    "Chinese (Simplified)"),
}

# deep_translator için dil kodu uyarlamaları
_GOOGLE_LANG_MAP = {
    "zh": "zh-CN",
    "ja": "ja",
    "ko": "ko",
    "bn": "bn",
    "ur": "ur",
    "vi": "vi",
    "hi": "hi",
    "ar": "ar",
}

# ── Giyim stil tipleri ─────────────────────────────────────────────────────────
GIYIM_STYLE = {
    "kararlı":      "power-authoritative",
    "güvenilir":    "classic-trustworthy",
    "dengeli":      "balanced-classic",
    "güçlü":        "power-authoritative",
    "lider":        "power-authoritative",
    "enerjik":      "dynamic-casual",
    "zarif":        "elegant-refined",
    "narin":        "soft-delicate",
    "sanatsal":     "creative-bohemian",
    "yaratıcı":     "creative-bohemian",
    "hassas":       "warm-natural",
    "çekici":       "elegant-refined",
    "uyumlu":       "balanced-classic",
    "sosyal":       "dynamic-casual",
    "cazip":        "elegant-refined",
    "pratik":       "minimal-functional",
    "dikkatli":     "minimal-functional",
    "analitik":     "minimal-functional",
    "odaklı":       "minimal-functional",
    "sezgisel":     "warm-natural",
    "açık_kalpli":  "warm-natural",
}

COLOR_PALETTES = {
    "power-authoritative": {
        "ana":    ["#000000", "#1A1A1A", "#2D004D", "#8B0000"],
        "vurgu":  ["#FFD700", "#C0C0C0"],
        "kacin":  ["pastel colors", "light tones"],
    },
    "classic-trustworthy": {
        "ana":    ["#1F3A5F", "#2E4A2E", "#4A3728", "#36454F"],
        "vurgu":  ["#B8860B", "#708090"],
        "kacin":  ["neon colors", "overly bright patterns"],
    },
    "balanced-classic": {
        "ana":    ["#3B4A6B", "#4A5568", "#2D6A4F", "#5C4033"],
        "vurgu":  ["#D4AF37", "#8FA3A8"],
        "kacin":  ["extreme patterns", "clashing colors"],
    },
    "dynamic-casual": {
        "ana":    ["#1A73E8", "#E65100", "#2E7D32", "#AD1457"],
        "vurgu":  ["#FFB300", "#FFFFFF"],
        "kacin":  ["overly formal", "restrictive cuts"],
    },
    "elegant-refined": {
        "ana":    ["#2C2C2C", "#E8D5B7", "#C9A97A", "#8B6F47"],
        "vurgu":  ["#D4AF37", "#F5F5F5"],
        "kacin":  ["loud prints", "casual sportswear"],
    },
    "soft-delicate": {
        "ana":    ["#F3E5F5", "#E8F5E9", "#FFF8E1", "#FCE4EC"],
        "vurgu":  ["#CE93D8", "#A5D6A7"],
        "kacin":  ["heavy fabrics", "very dark colors"],
    },
    "creative-bohemian": {
        "ana":    ["#6A1B9A", "#1565C0", "#2E7D32", "#E65100"],
        "vurgu":  ["#FFD740", "#FF6D00"],
        "kacin":  ["overly corporate", "plain minimalism"],
    },
    "warm-natural": {
        "ana":    ["#795548", "#6D4C41", "#4CAF50", "#FF8A65"],
        "vurgu":  ["#FFB74D", "#A5D6A7"],
        "kacin":  ["cold grays", "harsh metallics"],
    },
    "minimal-functional": {
        "ana":    ["#37474F", "#455A64", "#546E7A", "#ECEFF1"],
        "vurgu":  ["#B0BEC5", "#FFFFFF"],
        "kacin":  ["loud patterns", "distracting accessories"],
    },
}

# ── Jenerik şablonlar ──────────────────────────────────────────────────────────
ASTROLOJI_TEMPLATE = """ℹ️ This module generates a personalized astrology map supported by Facesyma facial analysis data when the user's birth date and time are entered.

🪐 Planetary Influences
• Sun: Ego, identity, life purpose
• Moon: Emotions, inner world, habits
• Mercury: Communication, thought, learning
• Venus: Love, aesthetics, values
• Mars: Action, desire, anger management
• Jupiter: Growth, luck, wisdom
• Saturn: Responsibility, discipline, limits

🔮 Interpretations
Your {sifat} quality carries strong resonance with {sign} energy.
The alignment between your sun sign and the dominant traits in your facial analysis is remarkable."""

DOGUM_ANALIZI_TEMPLATE = """ℹ️ Calculated when birth date, time, and location are entered.

🔢 Numerology
• life_path: Core personality number — sum of birth date digits
• destiny: Numerical values of letters in your name
• soul_urge: Sum of vowels in your name
• personality: Sum of consonants in your name

⏰ Birth Hour Energy
• 01-06: Intuitive, spiritual — inward energy hours
• 07-11: Creative, initiating — ideal for starting new projects
• 12-17: Social, collaborative — ideal for teamwork and meetings
• 18-23: Analytical, planning — ideal for evaluation and strategy
• 00-01: Transformational — powerful moment for deep decisions"""

# ── İlerleme yönetimi ──────────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

# ── Groq yardımcı ─────────────────────────────────────────────────────────────
def call_groq(prompt: str, max_tokens: int = 600, retries: int = 3, model: str = None) -> str:
    use_model = model or MODEL_SMART
    for attempt in range(retries):
        try:
            time.sleep(REQUEST_DELAY)
            response = groq_client.chat.completions.create(
                model=use_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err:
                wait = 45 * (attempt + 1)
                print(f"  Rate limit — {wait}s bekleniyor... (deneme {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                print(f"  Groq hata (deneme {attempt+1}): {e}")
                time.sleep(5)
    return ""

# ── Google Translate yardımcıları ──────────────────────────────────────────────
def _translate_text_google(text: str, target_lang: str) -> str:
    """Google Translate ile metin çevirir. Uzun metinler için paragraf bazlı bölme."""
    if not _GOOGLE_TRANSLATE_AVAILABLE or not text or not text.strip():
        return text
    mapped = _GOOGLE_LANG_MAP.get(target_lang, target_lang)
    SEP = chr(10) + chr(10)
    MAX_CHUNK = 4800

    if len(text) <= MAX_CHUNK:
        try:
            result = GoogleTranslator(source="en", target=mapped).translate(text)
            return result or text
        except Exception as e:
            print(f"    Google Translate hata: {e}")
            return text

    paragraphs = text.split(SEP)
    chunks, current, current_len = [], [], 0
    for para in paragraphs:
        if current_len + len(para) + 2 > MAX_CHUNK and current:
            chunks.append(SEP.join(current))
            current, current_len = [para], len(para)
        else:
            current.append(para)
            current_len += len(para) + 2
    if current:
        chunks.append(SEP.join(current))

    translated_chunks = []
    for chunk in chunks:
        try:
            translated_chunks.append(GoogleTranslator(source="en", target=mapped).translate(chunk) or chunk)
            time.sleep(0.5)
        except Exception as e:
            print(f"    Google Translate chunk hata: {e}")
            translated_chunks.append(chunk)
    return SEP.join(translated_chunks)


def _translate_dict_recursive(data, target_lang: str):
    """Nested dict/list içindeki tüm string değerleri Google Translate ile çevirir."""
    if isinstance(data, str):
        return _translate_text_google(data, target_lang)
    elif isinstance(data, dict):
        return {k: _translate_dict_recursive(v, target_lang) for k, v in data.items()}
    elif isinstance(data, list):
        return [_translate_dict_recursive(item, target_lang) for item in data]
    return data

# ── Tip A: Metin modül promptları ─────────────────────────────────────────────
MODULE_PROMPTS = {
    "title": lambda trait, trait_en: (
        f'Generate a short coaching profile title (max 6 words) for someone with a "{trait_en}" personality trait. '
        f'Example format: "Determined Personality Profile". Return ONLY the title, nothing else.'
    ),
    "description": lambda trait, trait_en: (
        f'Write one sentence (max 20 words) describing a person with a "{trait_en}" personality trait for a face analysis app. '
        f'Return ONLY the sentence.'
    ),
    "yas_koc_ozet": lambda trait, trait_en: (
        f'Write a life coaching overview in English for someone with a "{trait_en}" personality trait. '
        f'Use EXACTLY this format with these emoji headers:\n\n'
        f'Your facial features and life coach evaluation present the following picture:\n\n'
        f'📊 Life Areas\n'
        f'🧠 Mental: [one line]\n'
        f'❤️ Emotional: [one line]\n'
        f'💼 Career: [one line]\n'
        f'🌿 Health: [one line]\n'
        f'🤝 Relationships: [one line]\n'
        f'🎯 Purpose: [one line]\n\n'
        f'🎯 Action Plan\n'
        f'This week: [one concrete action]\n'
        f'This month: [one concrete action]\n'
        f'This year: [one concrete action]\n\n'
        f'Keep it under 200 words total. Return ONLY the text.'
    ),
    "iletisim_becerileri": lambda trait, trait_en: (
        f'Write a communication skills profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🗣️ Communication Style\n[2 sentences describing their communication style]\n\n'
        f'💪 Strengths\n[2 specific communication strengths]\n\n'
        f'📈 Growth Steps\n[2 actionable improvement tips]\n\n'
        f'💻 Digital Communication\n[1 tip for written/digital communication]\n\n'
        f'Keep it under 120 words. Return ONLY the text.'
    ),
    "ozguven": lambda trait, trait_en: (
        f'Write a self-confidence profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'📊 Current Level\n[1-2 sentences about confidence level]\n\n'
        f'🎯 Practical Steps\n[2 concrete confidence-building tips]\n\n'
        f'🧍 Body Language\n[1 body language tip]\n\n'
        f'Keep it under 80 words. Return ONLY the text.'
    ),
    "stres_yonetimi": lambda trait, trait_en: (
        f'Write a stress management profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🔴 Triggers\n[2 specific stress triggers for this personality]\n\n'
        f'💚 Coping Methods\n[2 specific coping strategies]\n\n'
        f'🔵 Long-term Strategies\n[1 long-term strategy]\n\n'
        f'Keep it under 100 words. Return ONLY the text.'
    ),
    "iliski_yonetimi": lambda trait, trait_en: (
        f'Write a relationship management profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'💑 Relationship Style\n[2 sentences about their relationship approach]\n\n'
        f'💪 Strengths\n[2 relationship strengths]\n\n'
        f'⚠️ Challenges\n[1 relationship challenge to be aware of]\n\n'
        f'✅ Recommendations\n[2 practical relationship tips]\n\n'
        f'Keep it under 110 words. Return ONLY the text.'
    ),
    "vucut_dil": lambda trait, trait_en: (
        f'Write a body language profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'😊 Facial Expression\n[2 sentences about facial expression tendencies]\n\n'
        f'🧍 Posture Tips\n[2 posture and body language tips]\n\n'
        f'💼 Professional Setting\n[2 tips for professional body language]\n\n'
        f'Keep it under 100 words. Return ONLY the text.'
    ),
    "kisisel_hedefler": lambda trait, trait_en: (
        f'Write a personal goals profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🎯 Short-term (1-3 months)\n[1 specific short-term goal/action]\n\n'
        f'📅 Mid-term (3-12 months)\n[1 specific mid-term goal]\n\n'
        f'🚀 Long-term (1-5 years)\n[1 long-term development goal]\n\n'
        f'💪 Overcoming Obstacles\n[1 motivational insight]\n\n'
        f'Keep it under 90 words. Return ONLY the text.'
    ),
    "zaman_yonetimi": lambda trait, trait_en: (
        f'Write a time management profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'⏰ Time Style\n[2 sentences about their time management approach]\n\n'
        f'🛠️ Techniques\n[2 specific time management techniques suited to them]\n\n'
        f'⚠️ Pitfalls\n[1 time management pitfall to watch]\n\n'
        f'Keep it under 80 words. Return ONLY the text.'
    ),
    "saglik_esenwlik": lambda trait, trait_en: (
        f'Write a health and wellness profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🌿 Strengths\n[2 health-related strengths of this personality]\n\n'
        f'📈 Growth Areas\n[2 specific wellness areas to develop]\n\n'
        f'⚠️ Watch Out\n[1 health risk to be aware of]\n\n'
        f'✅ Practical Steps\n[2 concrete daily health habits]\n\n'
        f'Keep it under 120 words. Return ONLY the text.'
    ),
    "guvenlik": lambda trait, trait_en: (
        f'Write a personal security profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🛡️ Personal Security\n[1-2 sentences about their natural security mindset]\n\n'
        f'💙 Emotional Security\n[1-2 sentences about emotional security needs]\n\n'
        f'💰 Financial Security\n[1-2 sentences about financial approach]\n\n'
        f'✅ Recommendations\n[2 practical security tips]\n\n'
        f'Keep it under 110 words. Return ONLY the text.'
    ),
    "dogruluk_sadakat": lambda trait, trait_en: (
        f'Write a loyalty and honesty profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🔍 Profile\n[2 sentences about their loyalty and honesty approach]\n\n'
        f'💪 Strengths\n[2 loyalty/honesty strengths]\n\n'
        f'⚠️ Watch Out\n[1 loyalty-related challenge]\n\n'
        f'Keep it under 80 words. Return ONLY the text.'
    ),
    "suc_egilim": lambda trait, trait_en: (
        f'Write a risk profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'📊 Risk Profile\n[1-2 sentences about potential social friction points]\n\n'
        f'🛡️ Protective Factors\n[2 factors that reduce risk for this personality]\n\n'
        f'💡 Recommendations\n[1 constructive channeling suggestion]\n\n'
        f'⚕️ Note: This analysis is not diagnostic. Consult a professional for clinical evaluation.\n\n'
        f'Keep it under 90 words. Return ONLY the text.'
    ),
    # ── Yeni Tip A modüller ──────────────────────────────────────────────────────
    "etkinlik_tavsiye": lambda trait, trait_en: (
        f'Write activity and event recommendations in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🎯 Why These Activities Suit You\n'
        f'[2 sentences: explain specifically why these activities match the {trait_en} personality — be concrete]\n\n'
        f'🌟 Top Activities\n'
        f'• [Activity 1]: [why this suits {trait_en} personality]\n'
        f'• [Activity 2]: [why this suits {trait_en} personality]\n'
        f'• [Activity 3]: [why this suits {trait_en} personality]\n\n'
        f'🌿 Outdoor Option\n'
        f'• [Outdoor activity]: [why it suits {trait_en} personality]\n\n'
        f'🏠 Indoor Option\n'
        f'• [Indoor activity]: [why it suits {trait_en} personality]\n\n'
        f'Keep it under 120 words. Return ONLY the text.'
    ),
    "spor_aktivite": lambda trait, trait_en: (
        f'Write sport and physical activity recommendations in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'💪 Why These Sports Suit You\n'
        f'[1-2 sentences: explain specifically why these sports match the {trait_en} personality]\n\n'
        f'🏃 Recommended Sports\n'
        f'• [Sport 1]: [why it fits {trait_en} personality]\n'
        f'• [Sport 2]: [why it fits {trait_en} personality]\n'
        f'• [Sport 3]: [why it fits {trait_en} personality]\n\n'
        f'⏱️ Ideal Training Style\n'
        f'[1-2 sentences about training approach suited to this personality]\n\n'
        f'⚠️ Avoid\n'
        f'[1 type of exercise that may not suit {trait_en} personality and why]\n\n'
        f'Keep it under 100 words. Return ONLY the text.'
    ),
    "kariyer_yolu": lambda trait, trait_en: (
        f'Write a career path profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🎯 Natural Career Direction\n'
        f'[2 sentences about their natural career inclinations — specific to {trait_en} personality]\n\n'
        f'💼 Best-Fit Roles\n'
        f'• [Role 1]: [why this suits {trait_en} personality]\n'
        f'• [Role 2]: [why this suits {trait_en} personality]\n'
        f'• [Role 3]: [why this suits {trait_en} personality]\n\n'
        f'📈 Growth Strategy\n'
        f'[2 sentences about career development approach]\n\n'
        f'⚠️ Environments to Avoid\n'
        f'[1 work environment that does not suit {trait_en} personality and why]\n\n'
        f'Keep it under 120 words. Return ONLY the text.'
    ),
    "insan_kaynaklari": lambda trait, trait_en: (
        f'Write a human resources and teamwork profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🤝 Team Dynamic\n'
        f'[2 sentences about their role and unique value in teams — specific to {trait_en} personality]\n\n'
        f'💪 HR Strengths\n'
        f'• [Strength 1 as colleague/team member for {trait_en} personality]\n'
        f'• [Strength 2 as colleague/team member]\n\n'
        f'📊 Leadership Style\n'
        f'[1-2 sentences about their natural leadership or contribution approach]\n\n'
        f'✅ Collaboration Tips\n'
        f'• [Tip 1 for working better with others]\n'
        f'• [Tip 2 for working better with others]\n\n'
        f'Keep it under 100 words. Return ONLY the text.'
    ),
    "duygusal_ruhsal": lambda trait, trait_en: (
        f'Write an emotional and spiritual development profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🌱 Emotional Core\n'
        f'[2 sentences about their emotional nature and inner world — specific to {trait_en} personality]\n\n'
        f'💙 Emotional Strengths\n'
        f'• [Strength 1 that {trait_en} personality naturally has]\n'
        f'• [Strength 2]\n\n'
        f'🔮 Spiritual Path\n'
        f'[2 sentences about spiritual or growth practices that resonate with {trait_en} personality]\n\n'
        f'✨ Daily Practice\n'
        f'[1 specific daily emotional/spiritual practice perfectly suited to {trait_en} personality]\n\n'
        f'Keep it under 90 words. Return ONLY the text.'
    ),
    "meditasyon_egzersiz": lambda trait, trait_en: (
        f'Write a meditation and mindfulness exercise profile in English for someone with a "{trait_en}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🧘 Why This Works for You\n'
        f'[1-2 sentences: explain specifically why meditation/mindfulness suits {trait_en} personality]\n\n'
        f'🌟 Best Practices\n'
        f'• [Practice 1]: [why it suits {trait_en} personality]\n'
        f'• [Practice 2]: [why it suits {trait_en} personality]\n\n'
        f'⏰ Timing\n'
        f'[1 sentence about ideal time and duration for {trait_en} personality]\n\n'
        f'🌬️ Breathing Technique\n'
        f'[1 specific breathing technique best suited to {trait_en} personality and why]\n\n'
        f'Keep it under 80 words. Return ONLY the text.'
    ),
}

# ── Tip B: Yapılandırılmış dict modülleri ──────────────────────────────────────
# Her modülde "neden" alanı bulunur: önerinin NEDEN bu sıfata uygun olduğunu açıklar.
# Bu alan gelecekteki RAG / vector embedding aramaları için kritik semantik bağlantıdır.

def _parse_json_safe(raw: str, fallback: dict) -> dict:
    """Groq çıktısından JSON çıkartır; başarısız olursa fallback döner."""
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else fallback
    except Exception:
        return fallback


def generate_giyim_en(trait_en: str, style_type: str) -> dict:
    palette = COLOR_PALETTES.get(style_type, COLOR_PALETTES["balanced-classic"])
    prompt = (
        f'Write a clothing coaching profile for someone with a "{trait_en}" personality and "{style_type}" style. '
        f'Provide 4 sections:\n'
        f'1. Philosophy (2 sentences about their core style philosophy)\n'
        f'2. Combination (2-3 sentences about ideal outfit combinations)\n'
        f'3. Color Psychology (2 sentences about their ideal colors)\n'
        f'4. Lifestyle Adaptation (2 sentences about practical daily style tips)\n\n'
        f'Return ONLY a JSON object with keys: "felsefe", "kombinasyon", "renk_psikolojisi", "yasam_uyarlamasi". '
        f'Each value is a string. No markdown, no extra text.'
    )
    raw = call_groq(prompt, max_tokens=400)
    fallback = {
        "felsefe": f"{trait_en.capitalize()} personality dresses to express authenticity.",
        "kombinasyon": "Choose pieces that reflect your natural character.",
        "renk_psikolojisi": "Colors that align with your personality speak louder.",
        "yasam_uyarlamasi": "Every outfit should feel like an extension of who you are.",
    }
    coaching = _parse_json_safe(raw, fallback)
    return {
        "stil_tipi": style_type,
        "coaching":  coaching,
        "renk_paleti": palette,
        "yuz_sekli_notu": {
            "oval":      "Most cuts work; V-neck and long necklaces are recommended.",
            "kare":      "Soft rounded necklines balance angular features.",
            "yuvarlak":  "V-neck and vertical lines elongate the face.",
            "kalp":      "Wide shoulder lines balance the lower face.",
            "uzun":      "Horizontal lines and high necklines balance proportions.",
            "elmas":     "Wide necklines and A-line skirts balance the structure.",
        },
    }


def generate_kitap_en(trait_en: str) -> dict:
    prompt = (
        f'Generate book recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why these specific book genres particularly resonate with the {trait_en} personality — be concrete",'
        f'"kategoriler": ['
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this specific genre suits {trait_en} personality", "oneriler": ["Title by Author", "Title by Author", "Title by Author"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this specific genre suits {trait_en} personality", "oneriler": ["Title by Author", "Title by Author", "Title by Author"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this specific genre suits {trait_en} personality", "oneriler": ["Title by Author", "Title by Author", "Title by Author"]}}'
        f'],'
        f'"okuma_stili": "1-2 sentences: how {trait_en} personality reads and engages with books"}}'
    )
    raw = call_groq(prompt, max_tokens=700)
    fallback = {
        "neden": f"Books complement the {trait_en} personality's natural curiosity and growth mindset.",
        "kategoriler": [
            {"tur": "Personal Development", "neden": f"Aligns with {trait_en} personality's drive for self-improvement.", "oneriler": ["Atomic Habits by James Clear", "Mindset by Carol Dweck", "The Power of Now by Eckhart Tolle"]},
            {"tur": "Biography", "neden": f"Inspires {trait_en} personality through real-life stories.", "oneriler": ["Leonardo da Vinci by Walter Isaacson", "Long Walk to Freedom by Nelson Mandela", "Educated by Tara Westover"]},
            {"tur": "Philosophy", "neden": f"Feeds {trait_en} personality's depth and contemplative nature.", "oneriler": ["Meditations by Marcus Aurelius", "Man's Search for Meaning by Viktor Frankl", "The Alchemist by Paulo Coelho"]},
        ],
        "okuma_stili": f"The {trait_en} personality reads deeply, often returning to passages that resonate.",
    }
    return _parse_json_safe(raw, fallback)


def generate_film_en(trait_en: str) -> dict:
    prompt = (
        f'Generate film and series recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why these specific film genres appeal to the {trait_en} personality — be concrete",'
        f'"kategoriler": ['
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre resonates with {trait_en} personality", "oneriler": ["Film Title (Year)", "Film Title (Year)", "Film Title (Year)"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre resonates with {trait_en} personality", "oneriler": ["Film Title (Year)", "Film Title (Year)", "Film Title (Year)"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre resonates with {trait_en} personality", "oneriler": ["Film Title (Year)", "Film Title (Year)", "Film Title (Year)"]}}'
        f'],'
        f'"izleme_stili": "1-2 sentences: how {trait_en} personality watches and processes films"}}'
    )
    raw = call_groq(prompt, max_tokens=700)
    fallback = {
        "neden": f"Films that reflect depth and complexity resonate with the {trait_en} personality.",
        "kategoriler": [
            {"tur": "Drama", "neden": f"Speaks to the {trait_en} personality's emotional depth.", "oneriler": ["The Shawshank Redemption (1994)", "Schindler's List (1993)", "Good Will Hunting (1997)"]},
            {"tur": "Documentary", "neden": f"Feeds {trait_en} personality's need for real-world insight.", "oneriler": ["Free Solo (2018)", "13th (2016)", "Jiro Dreams of Sushi (2011)"]},
            {"tur": "Thriller", "neden": f"Engages {trait_en} personality's analytical mind.", "oneriler": ["Inception (2010)", "Parasite (2019)", "Gone Girl (2014)"]},
        ],
        "izleme_stili": f"The {trait_en} personality watches attentively and enjoys post-film reflection.",
    }
    return _parse_json_safe(raw, fallback)


def generate_muzik_en(trait_en: str) -> dict:
    prompt = (
        f'Generate music recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why this music style suits the {trait_en} personality — be concrete",'
        f'"turler": ['
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre suits {trait_en} personality specifically", "sanatcilar": ["Artist 1", "Artist 2", "Artist 3"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre suits {trait_en} personality specifically", "sanatcilar": ["Artist 1", "Artist 2", "Artist 3"]}},'
        f'{{"tur": "Genre Name", "neden": "1 sentence: why this genre suits {trait_en} personality specifically", "sanatcilar": ["Artist 1", "Artist 2", "Artist 3"]}}'
        f'],'
        f'"dinleme_stili": "1-2 sentences: how {trait_en} personality engages with music"}}'
    )
    raw = call_groq(prompt, max_tokens=600)
    fallback = {
        "neden": f"Music is a powerful channel for the {trait_en} personality's inner world.",
        "turler": [
            {"tur": "Classical", "neden": f"Mirrors the {trait_en} personality's structured inner world.", "sanatcilar": ["Ludwig van Beethoven", "Johann Sebastian Bach", "Frédéric Chopin"]},
            {"tur": "Jazz", "neden": f"Matches the {trait_en} personality's improvisational thinking.", "sanatcilar": ["Miles Davis", "John Coltrane", "Norah Jones"]},
            {"tur": "Indie", "neden": f"Speaks to {trait_en} personality's authentic self-expression.", "sanatcilar": ["Bon Iver", "Sufjan Stevens", "Phoebe Bridgers"]},
        ],
        "dinleme_stili": f"The {trait_en} personality listens deeply, connecting music to emotional states.",
    }
    return _parse_json_safe(raw, fallback)


def generate_podcast_en(trait_en: str) -> dict:
    prompt = (
        f'Generate podcast recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why these podcast categories suit the {trait_en} personality — be concrete",'
        f'"kategoriler": ['
        f'{{"tur": "Category Name", "neden": "1 sentence: why this category resonates with {trait_en} personality", "oneriler": ["Podcast Name", "Podcast Name", "Podcast Name"]}},'
        f'{{"tur": "Category Name", "neden": "1 sentence: why this category resonates with {trait_en} personality", "oneriler": ["Podcast Name", "Podcast Name", "Podcast Name"]}},'
        f'{{"tur": "Category Name", "neden": "1 sentence: why this category resonates with {trait_en} personality", "oneriler": ["Podcast Name", "Podcast Name", "Podcast Name"]}}'
        f']}}'
    )
    raw = call_groq(prompt, max_tokens=600)
    fallback = {
        "neden": f"Podcasts offer the {trait_en} personality meaningful content to grow and reflect.",
        "kategoriler": [
            {"tur": "Personal Development", "neden": f"Supports {trait_en} personality's growth orientation.", "oneriler": ["The Tim Ferriss Show", "Dare to Lead with Brené Brown", "The School of Greatness"]},
            {"tur": "Science & Technology", "neden": f"Feeds {trait_en} personality's intellectual curiosity.", "oneriler": ["Lex Fridman Podcast", "Radiolab", "Hidden Brain"]},
            {"tur": "Mindfulness", "neden": f"Grounds the {trait_en} personality's inner experience.", "oneriler": ["On Being with Krista Tippett", "10% Happier", "The Daily Meditation Podcast"]},
        ],
    }
    return _parse_json_safe(raw, fallback)


def generate_seyahat_en(trait_en: str) -> dict:
    prompt = (
        f'Generate travel recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why this travel style suits the {trait_en} personality — be concrete",'
        f'"destinasyon_tipi": ["Type 1", "Type 2", "Type 3"],'
        f'"aktiviteler": ['
        f'{{"aktivite": "Activity name", "neden": "1 sentence: why this activity suits {trait_en} personality"}},'
        f'{{"aktivite": "Activity name", "neden": "1 sentence: why this activity suits {trait_en} personality"}},'
        f'{{"aktivite": "Activity name", "neden": "1 sentence: why this activity suits {trait_en} personality"}}'
        f'],'
        f'"seyahat_stili": "1-2 sentences: how {trait_en} personality travels and experiences destinations"}}'
    )
    raw = call_groq(prompt, max_tokens=600)
    fallback = {
        "neden": f"Travel enriches the {trait_en} personality through meaningful exploration.",
        "destinasyon_tipi": ["Cultural cities", "Nature retreats", "Historical sites"],
        "aktiviteler": [
            {"aktivite": "Museum visits", "neden": f"Satisfies {trait_en} personality's curiosity and love of depth."},
            {"aktivite": "Hiking", "neden": f"Gives {trait_en} personality space for reflection and challenge."},
            {"aktivite": "Local cuisine tours", "neden": f"Connects {trait_en} personality to authentic local experiences."},
        ],
        "seyahat_stili": f"The {trait_en} personality travels with intention, seeking meaning over luxury.",
    }
    return _parse_json_safe(raw, fallback)


def generate_afirasyon_en(trait_en: str) -> dict:
    prompt = (
        f'Generate daily affirmations specifically crafted for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why these affirmations are specifically designed for {trait_en} personality and how they address their unique inner dynamics",'
        f'"sabah": "A powerful morning affirmation written specifically for {trait_en} personality (1-2 sentences)",'
        f'"aksam": "A grounding evening affirmation written specifically for {trait_en} personality (1-2 sentences)",'
        f'"haftalik": ['
        f'"Monday affirmation for {trait_en} personality",'
        f'"Tuesday affirmation for {trait_en} personality",'
        f'"Wednesday affirmation for {trait_en} personality",'
        f'"Thursday affirmation for {trait_en} personality",'
        f'"Friday affirmation for {trait_en} personality",'
        f'"Saturday affirmation for {trait_en} personality",'
        f'"Sunday affirmation for {trait_en} personality"'
        f']}}'
    )
    raw = call_groq(prompt, max_tokens=700)
    fallback = {
        "neden": f"These affirmations are crafted to strengthen the unique qualities of the {trait_en} personality.",
        "sabah": f"I embrace my {trait_en} nature and move through the day with confidence and purpose.",
        "aksam": f"I honor the depth I brought today and release what no longer serves my growth.",
        "haftalik": [
            f"My {trait_en} spirit leads me toward my highest potential.",
            f"I trust my natural strengths to guide my path.",
            f"Every challenge sharpens my {trait_en} character.",
            f"I am worthy of all the good that comes my way.",
            f"My unique perspective creates value in the world.",
            f"I nurture my gifts and share them generously.",
            f"I rest in the knowledge of who I truly am.",
        ],
    }
    return _parse_json_safe(raw, fallback)


def generate_saglik_tavsiye_en(trait_en: str) -> dict:
    prompt = (
        f'Generate structured health recommendations for someone with a "{trait_en}" personality. '
        f'Return ONLY a valid JSON object with EXACTLY this structure (no markdown, no extra text):\n'
        f'{{"neden": "2 sentences: why this health approach specifically suits the {trait_en} personality — be concrete about the personality-health connection",'
        f'"beslenme": {{"tavsiye": "Specific nutrition advice for {trait_en} personality", "neden": "Why this nutrition approach particularly suits {trait_en} personality"}},'
        f'"hareket": {{"tavsiye": "Specific movement or exercise advice for {trait_en} personality", "neden": "Why this movement style aligns with {trait_en} personality"}},'
        f'"uyku": {{"tavsiye": "Specific sleep routine advice for {trait_en} personality", "neden": "Why this sleep approach works for {trait_en} personality"}},'
        f'"zihin": {{"tavsiye": "Specific mental health practice for {trait_en} personality", "neden": "Why this mental practice resonates with {trait_en} personality"}}}}'
    )
    raw = call_groq(prompt, max_tokens=700)
    fallback = {
        "neden": f"The {trait_en} personality's health approach should support both their physical vitality and mental clarity.",
        "beslenme": {"tavsiye": "Prioritize whole foods with regular meal timing to support steady energy.", "neden": f"Supports {trait_en} personality's need for consistent performance."},
        "hareket": {"tavsiye": "Combine strength training with mindful movement practices.", "neden": f"Balances {trait_en} personality's active nature with restorative practice."},
        "uyku": {"tavsiye": "Maintain a consistent 7-8 hour sleep schedule with a wind-down ritual.", "neden": f"Helps {trait_en} personality process and integrate their rich inner experience."},
        "zihin": {"tavsiye": "Practice daily journaling and regular social connection.", "neden": f"Gives {trait_en} personality a healthy outlet for their depth and sensitivity."},
    }
    return _parse_json_safe(raw, fallback)


# ── Modül listeleri ────────────────────────────────────────────────────────────
# TEXT_MODULES: çeviri için düz string alanları
TEXT_MODULES = list(MODULE_PROMPTS.keys()) + ["astroloji_harita", "dogum_analizi"]

# DICT_MODULES: recursive dict çevirisi gereken modüller
DICT_MODULES = ["giyim", "kitap_tavsiye", "film_tavsiye", "muzik_tavsiye",
                "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon", "saglik_tavsiye"]


# ── İngilizce modül üretimi ────────────────────────────────────────────────────
def generate_en_modules(trait_tr: str, trait_en: str) -> dict:
    """Bir sıfat için tüm İngilizce modülleri üretir."""
    style_type = GIYIM_STYLE.get(trait_tr, "balanced-classic")
    doc = {
        "_id":              trait_tr,
        "lang":             "en",
        "updated_at":       datetime.now(timezone.utc).isoformat(),
        "astroloji_harita": ASTROLOJI_TEMPLATE.replace("{sifat}", trait_en),
        "dogum_analizi":    DOGUM_ANALIZI_TEMPLATE,
    }

    # Tip A: TEXT modüller (Groq)
    for mod_name, prompt_fn in MODULE_PROMPTS.items():
        print(f"  [{trait_tr}] {mod_name} üretiliyor...")
        prompt = prompt_fn(trait_tr, trait_en)
        content = call_groq(prompt, max_tokens=500, model=MODEL_SMART)
        doc[mod_name] = content

    # Tip B: DICT modüller (Groq → JSON)
    print(f"  [{trait_tr}] giyim üretiliyor...")
    doc["giyim"] = generate_giyim_en(trait_en, style_type)

    print(f"  [{trait_tr}] kitap_tavsiye üretiliyor...")
    doc["kitap_tavsiye"] = generate_kitap_en(trait_en)

    print(f"  [{trait_tr}] film_tavsiye üretiliyor...")
    doc["film_tavsiye"] = generate_film_en(trait_en)

    print(f"  [{trait_tr}] muzik_tavsiye üretiliyor...")
    doc["muzik_tavsiye"] = generate_muzik_en(trait_en)

    print(f"  [{trait_tr}] podcast_tavsiye üretiliyor...")
    doc["podcast_tavsiye"] = generate_podcast_en(trait_en)

    print(f"  [{trait_tr}] seyahat_tavsiye üretiliyor...")
    doc["seyahat_tavsiye"] = generate_seyahat_en(trait_en)

    print(f"  [{trait_tr}] gunluk_afirasyon üretiliyor...")
    doc["gunluk_afirasyon"] = generate_afirasyon_en(trait_en)

    print(f"  [{trait_tr}] saglik_tavsiye üretiliyor...")
    doc["saglik_tavsiye"] = generate_saglik_tavsiye_en(trait_en)

    return doc


# ── Türkçe native üretimi ──────────────────────────────────────────────────────
def generate_tr_modules(trait_tr: str, trait_en: str, en_doc: dict) -> dict:
    """Türkçe: title + description native Groq, geri kalan Google Translate."""
    doc = dict(en_doc)
    doc["lang"]       = "tr"
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    title_prompt = (
        f'"{trait_tr}" kişilik özelliğine sahip biri için kısa bir koçluk profil başlığı yaz (max 6 kelime). '
        f'Sadece başlığı döndür, başka hiçbir şey ekleme.'
    )
    desc_prompt = (
        f'Yüz analizi uygulaması için "{trait_tr}" kişilik özelliğine sahip birini tek cümleyle tanımla (max 20 kelime). '
        f'Sadece cümleyi döndür.'
    )

    print(f"  [TR] Başlık (native Groq) üretiliyor...")
    tr_title = call_groq(title_prompt, max_tokens=50)
    if tr_title:
        doc["title"] = tr_title

    print(f"  [TR] Açıklama (native Groq) üretiliyor...")
    tr_desc = call_groq(desc_prompt, max_tokens=80)
    if tr_desc:
        doc["description"] = tr_desc

    for key in TEXT_MODULES:
        if key in ("title", "description"):
            continue
        if key in doc and isinstance(doc[key], str):
            print(f"  [TR] {key} (Google Translate)...")
            doc[key] = _translate_text_google(doc[key], "tr")
            time.sleep(0.3)

    for key in DICT_MODULES:
        if key in doc:
            print(f"  [TR] {key} (dict → Google Translate)...")
            doc[key] = _translate_dict_recursive(doc[key], "tr")

    return doc


# ── Diğer dillere çeviri ───────────────────────────────────────────────────────
def translate_doc_to_lang(en_doc: dict, target_lang_code: str) -> dict:
    """İngilizce dökümanı hedef dile Google Translate ile çevirir."""
    doc = dict(en_doc)
    doc["lang"]       = target_lang_code
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()

    for key in TEXT_MODULES:
        if key in doc and isinstance(doc[key], str):
            print(f"    {key} (Google Translate)...")
            doc[key] = _translate_text_google(doc[key], target_lang_code)
            time.sleep(0.3)

    for key in DICT_MODULES:
        if key in doc:
            print(f"    {key} (dict → Google Translate)...")
            doc[key] = _translate_dict_recursive(doc[key], target_lang_code)

    return doc


# ── MongoDB kayıt ──────────────────────────────────────────────────────────────
def upsert_doc(collection_suffix: str, doc: dict):
    col = DB[f"coach_attributes_{collection_suffix}"]
    col.replace_one({"_id": doc["_id"]}, doc, upsert=True)


# ── Ana akış (3 faz) ───────────────────────────────────────────────────────────
def main():
    progress    = load_progress()
    total_sifat = len(SIFATLAR)

    for idx, (trait_tr, trait_en) in enumerate(SIFATLAR.items(), 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{total_sifat}] SIFAT: {trait_tr} ({trait_en})")
        print(f"{'='*60}")

        # FAZ 1: İngilizce üretim (Groq)
        en_key = f"{trait_tr}::en"
        if en_key in progress:
            print(f"  ✓ İngilizce zaten üretilmiş, yükleniyor...")
            en_doc = progress[en_key]
        else:
            print(f"  → FAZ 1: İngilizce modüller üretiliyor...")
            en_doc = generate_en_modules(trait_tr, trait_en)
            progress[en_key] = en_doc
            save_progress(progress)
            upsert_doc("en", en_doc)
            print(f"  ✓ İngilizce MongoDB'ye kaydedildi")

        # FAZ 2: Türkçe — native title/desc + Google Translate
        tr_key = f"{trait_tr}::tr"
        if tr_key in progress:
            print(f"  ✓ Türkçe zaten tamamlanmış")
        else:
            print(f"  → FAZ 2: Türkçe üretiliyor...")
            tr_doc = generate_tr_modules(trait_tr, trait_en, en_doc)
            tr_doc["_id"] = trait_tr
            upsert_doc("tr", tr_doc)
            progress[tr_key] = True
            save_progress(progress)
            print(f"  ✓ Türkçe kaydedildi")

        # FAZ 3: Diğer 16 dil — Google Translate
        for lang_code, (col_suffix, lang_full, _) in LANGUAGES.items():
            if lang_code in ("en", "tr"):
                continue

            lang_key = f"{trait_tr}::{lang_code}"
            if lang_key in progress:
                print(f"  ✓ {lang_full} zaten tamamlanmış")
                continue

            print(f"  → FAZ 3: {lang_full} çeviriliyor...")
            translated_doc = translate_doc_to_lang(en_doc, lang_code)
            translated_doc["_id"] = trait_tr
            upsert_doc(col_suffix, translated_doc)
            progress[lang_key] = True
            save_progress(progress)
            print(f"  ✓ {lang_full} kaydedildi")

        print(f"\n  ✅ [{trait_tr}] TAMAMLANDI")

    print(f"\n{'='*60}")
    print("TÜM SIFATLAR TAMAMLANDI")
    print(f"{'='*60}")

    print("\n📊 Doğrulama:")
    for lang_code, (col_suffix, lang_full, _) in LANGUAGES.items():
        col   = DB[f"coach_attributes_{col_suffix}"]
        count = col.count_documents({"_id": {"$in": list(SIFATLAR.keys())}})
        print(f"  {lang_full}: {count}/21 sıfat")


if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("HATA: GROQ_API_KEY env değişkeni eksik!")
        sys.exit(1)
    if not MONGO_URI:
        print("HATA: MONGO_URI env değişkeni eksik!")
        sys.exit(1)
    if not _GOOGLE_TRANSLATE_AVAILABLE:
        print("HATA: deep-translator yüklü değil. Çalıştır: pip install deep-translator")
        sys.exit(1)
    main()
