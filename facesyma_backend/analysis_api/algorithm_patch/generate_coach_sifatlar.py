"""
generate_coach_sifatlar.py
===========================
21 eksik sıfatı Coach DB'ye ekler.

Akış:
  1. Her sıfat için İngilizce modül içerikleri Groq ile üretilir.
  2. İngilizce içerikler Groq ile 17 dile çevrilir.
  3. Her dil için coach_attributes_{lang} koleksiyonuna upsert edilir.

Çalıştırma (ai_chat container içinde):
  python /tmp/generate_coach_sifatlar.py

İlerleme dosyası: /tmp/coach_gen_progress.json — kesintide devam sağlar.
"""

import os, json, time, re, sys
from datetime import datetime, timezone
from pymongo import MongoClient
from groq import Groq

# ── Config ─────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MONGO_URI    = os.environ.get("MONGO_URI", "")
MODEL_SMART   = "llama-3.3-70b-versatile"   # İngilizce üretim — daha kaliteli
MODEL_FAST    = "llama-3.1-8b-instant"      # Çeviri batch'leri — hızlı
PROGRESS_FILE = "/tmp/coach_gen_progress.json"
REQUEST_DELAY = 2.5   # saniye — 30 req/min altında kalır
BATCH_SIZE    = 3     # Çeviri başına max modül sayısı — token/min limitini aşmamak için
BATCH_DELAY   = 4.0   # Batch'ler arası ek bekleme (saniye)

groq_client  = Groq(api_key=GROQ_API_KEY)
MODEL        = MODEL_SMART  # backward compat alias (giyim fonksiyonu kullanıyor)
mongo_client = MongoClient(MONGO_URI)
DB           = mongo_client["facesyma-coach-backup"]

# ── 21 eksik sıfat ─────────────────────────────────────────────────────────────
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

# ── Dil haritası: {kod: (koleksiyon_suffix, tam_ad, groq_dil_adı)} ─────────────
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

# ── Giyim stil tipleri (sıfat bazlı) ──────────────────────────────────────────
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

# ── Jenerik şablonlar (sıfattan bağımsız içerik) ───────────────────────────────
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

# ── Groq yardımcı fonksiyonları ────────────────────────────────────────────────
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

# ── İngilizce modül üretimi ────────────────────────────────────────────────────
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
}

def generate_giyim_en(trait_en: str, style_type: str) -> dict:
    palette = COLOR_PALETTES.get(style_type, COLOR_PALETTES["balanced-classic"])
    prompt = (
        f'Write a clothing coaching profile for someone with a "{trait_en}" personality and "{style_type}" style. '
        f'Provide 3 sections:\n'
        f'1. Philosophy (2 sentences about their core style philosophy)\n'
        f'2. Combination (2-3 sentences about ideal outfit combinations)\n'
        f'3. Color Psychology (2 sentences about their ideal colors)\n'
        f'4. Lifestyle Adaptation (2 sentences about practical daily style tips)\n\n'
        f'Return ONLY a JSON object with keys: "felsefe", "kombinasyon", "renk_psikolojisi", "yasam_uyarlamasi". '
        f'Each value is a string. No markdown, no extra text.'
    )
    raw = call_groq(prompt, max_tokens=400)
    try:
        # JSON çıkartma denemesi
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        coaching = json.loads(m.group()) if m else {
            "felsefe": f"{trait_en.capitalize()} personality dresses to express authenticity.",
            "kombinasyon": "Choose pieces that reflect your natural character.",
            "renk_psikolojisi": "Colors that align with your personality speak louder.",
            "yasam_uyarlamasi": "Every outfit should feel like an extension of who you are.",
        }
    except Exception:
        coaching = {
            "felsefe": f"{trait_en.capitalize()} personality dresses to express authenticity.",
            "kombinasyon": "Choose pieces that reflect your natural character.",
            "renk_psikolojisi": "Colors that align with your personality speak louder.",
            "yasam_uyarlamasi": "Every outfit should feel like an extension of who you are.",
        }
    return {
        "stil_tipi": style_type,
        "coaching":  coaching,
        "renk_paleti": palette,
        "yuz_sekli_notu": {
            "oval":   "Most cuts work; V-neck and long necklaces are recommended.",
            "kare":   "Soft rounded necklines balance angular features.",
            "yuvarlak": "V-neck and vertical lines elongate the face.",
            "kalp":   "Wide shoulder lines balance the lower face.",
            "uzun":   "Horizontal lines and high necklines balance proportions.",
            "elmas":  "Wide necklines and A-line skirts balance the structure.",
        },
    }

def generate_en_modules(trait_tr: str, trait_en: str) -> dict:
    """Bir sıfat için tüm İngilizce modülleri üretir."""
    style_type = GIYIM_STYLE.get(trait_tr, "balanced-classic")
    doc = {
        "_id":         trait_tr,
        "lang":        "en",
        "updated_at":  datetime.now(timezone.utc).isoformat(),
        "astroloji_harita": ASTROLOJI_TEMPLATE.replace("{sifat}", trait_en),
        "dogum_analizi":    DOGUM_ANALIZI_TEMPLATE,
    }
    print(f"  [{trait_tr}] giyim üretiliyor...")
    doc["giyim"] = generate_giyim_en(trait_en, style_type)

    for mod_name, prompt_fn in MODULE_PROMPTS.items():
        print(f"  [{trait_tr}] {mod_name} üretiliyor...")
        prompt = prompt_fn(trait_tr, trait_en)
        content = call_groq(prompt, max_tokens=500, model=MODEL_SMART)
        doc[mod_name] = content
    return doc

# ── Çeviri ─────────────────────────────────────────────────────────────────────
TEXT_MODULES = list(MODULE_PROMPTS.keys()) + ["astroloji_harita", "dogum_analizi"]

def _translate_batch(batch: dict, target_lang_name: str) -> dict:
    """Küçük bir modül grubunu tek Groq çağrısıyla çevirir."""
    prompt = (
        f'Translate the following JSON values from English to {target_lang_name}. '
        f'Keep all emoji characters, formatting, line breaks, and section headers EXACTLY as they are. '
        f'Only translate the actual text content. '
        f'Return ONLY a valid JSON object with the same keys, no extra text:\n\n'
        f'{json.dumps(batch, ensure_ascii=False)}'
    )
    raw = call_groq(prompt, max_tokens=1400, model=MODEL_FAST)
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else {}
    except Exception:
        return {}

def translate_doc_to_lang(en_doc: dict, target_lang_name: str, target_lang_code: str) -> dict:
    """İngilizce dökümanı hedef dile çevirir — BATCH_SIZE'lık gruplar halinde."""
    to_translate = {k: en_doc[k] for k in TEXT_MODULES if k in en_doc and isinstance(en_doc[k], str)}
    keys = list(to_translate.keys())
    total_batches = (len(keys) + BATCH_SIZE - 1) // BATCH_SIZE
    translated = {}

    for i in range(0, len(keys), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch_keys = keys[i:i + BATCH_SIZE]
        batch = {k: to_translate[k] for k in batch_keys}
        print(f"    batch {batch_num}/{total_batches} ({', '.join(batch_keys)})...")
        result = _translate_batch(batch, target_lang_name)
        translated.update(result)
        if i + BATCH_SIZE < len(keys):
            time.sleep(BATCH_DELAY)

    doc = dict(en_doc)
    doc["lang"] = target_lang_code
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    for k, v in translated.items():
        if k in TEXT_MODULES and isinstance(v, str):
            doc[k] = v
    return doc

# ── MongoDB kayıt ──────────────────────────────────────────────────────────────
def upsert_doc(collection_suffix: str, doc: dict):
    col = DB[f"coach_attributes_{collection_suffix}"]
    col.replace_one({"_id": doc["_id"]}, doc, upsert=True)

# ── Ana akış ───────────────────────────────────────────────────────────────────
def main():
    progress = load_progress()
    total_sifat = len(SIFATLAR)

    for idx, (trait_tr, trait_en) in enumerate(SIFATLAR.items(), 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{total_sifat}] SIFAT: {trait_tr} ({trait_en})")
        print(f"{'='*60}")

        # 1. İngilizce üretim
        en_key = f"{trait_tr}::en"
        if en_key in progress:
            print(f"  ✓ İngilizce zaten üretilmiş, yükleniyor...")
            en_doc = progress[en_key]
        else:
            print(f"  → İngilizce modüller üretiliyor...")
            en_doc = generate_en_modules(trait_tr, trait_en)
            progress[en_key] = en_doc
            save_progress(progress)
            # İngilizce kaydet
            upsert_doc("en", en_doc)
            print(f"  ✓ İngilizce MongoDB'ye kaydedildi")

        # 2. Her dil için çeviri + kayıt
        for lang_code, (col_suffix, lang_full, groq_lang) in LANGUAGES.items():
            if lang_code == "en":
                continue  # zaten yapıldı

            lang_key = f"{trait_tr}::{lang_code}"
            if lang_key in progress:
                print(f"  ✓ {lang_full} zaten tamamlanmış")
                continue

            print(f"  → {lang_full} çeviriliyor...")
            translated_doc = translate_doc_to_lang(en_doc, groq_lang, lang_code)
            translated_doc["_id"] = trait_tr

            upsert_doc(col_suffix, translated_doc)
            progress[lang_key] = True
            save_progress(progress)
            print(f"  ✓ {lang_full} kaydedildi")

        print(f"\n  ✅ [{trait_tr}] TAMAMLANDI")

    print(f"\n{'='*60}")
    print("TÜM SIFATLAR TAMAMLANDI")
    print(f"{'='*60}")

    # Doğrulama
    print("\n📊 Doğrulama:")
    for lang_code, (col_suffix, lang_full, _) in LANGUAGES.items():
        col = DB[f"coach_attributes_{col_suffix}"]
        count = col.count_documents({"_id": {"$in": list(SIFATLAR.keys())}})
        print(f"  {lang_full}: {count}/21 sıfat eklendi")

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("HATA: GROQ_API_KEY env değişkeni eksik!")
        sys.exit(1)
    if not MONGO_URI:
        print("HATA: MONGO_URI env değişkeni eksik!")
        sys.exit(1)
    main()
