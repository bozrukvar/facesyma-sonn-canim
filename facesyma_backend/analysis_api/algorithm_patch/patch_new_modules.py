"""
patch_new_modules.py
=====================
Mevcut 21 sıfat dökümanlarına 13 yeni modülü ekler.
Mevcut alanları bozmaz — sadece eksik alanları ekler.

Çalıştırma (ai_chat container içinde):
  pip install deep-translator
  python /tmp/patch_new_modules.py

Yeni modüller:
  Tip A (text): etkinlik_tavsiye, spor_aktivite, kariyer_yolu,
                insan_kaynaklari, duygusal_ruhsal, meditasyon_egzersiz
  Tip B (dict): kitap_tavsiye, film_tavsiye, muzik_tavsiye,
                podcast_tavsiye, seyahat_tavsiye, gunluk_afirasyon, saglik_tavsiye

RAG Notu:
  Tip B modüllerin her öğesinde "neden" alanı bulunur.
  Bu alan önerinin NEDEN bu sıfata uygun olduğunu açıklar — RAG için kritik.
"""

import os, json, time, re, sys
from datetime import datetime, timezone
from pymongo import MongoClient
from groq import Groq

try:
    from deep_translator import GoogleTranslator
    _GT_OK = True
except ImportError:
    _GT_OK = False
    print("HATA: pip install deep-translator")
    sys.exit(1)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MONGO_URI    = os.environ.get("MONGO_URI", "")
PROGRESS_FILE = "/tmp/patch_progress.json"
MODEL_SMART  = "llama-3.3-70b-versatile"
REQUEST_DELAY = 2.5

groq_client  = Groq(api_key=GROQ_API_KEY)
mongo_client = MongoClient(MONGO_URI)
DB           = mongo_client["facesyma-coach-backup"]

SIFATLAR = {
    "kararlı": "determined", "güvenilir": "reliable", "dengeli": "balanced",
    "güçlü": "strong", "lider": "leader", "enerjik": "energetic",
    "zarif": "elegant", "narin": "delicate", "sanatsal": "artistic",
    "yaratıcı": "creative", "hassas": "sensitive", "çekici": "attractive",
    "uyumlu": "adaptable", "sosyal": "social", "cazip": "charming",
    "pratik": "practical", "dikkatli": "careful", "analitik": "analytical",
    "odaklı": "focused", "sezgisel": "intuitive", "açık_kalpli": "open-hearted",
}

LANGUAGES = {
    "en": "en", "tr": "tr", "ar": "ar", "de": "de", "ja": "jp",
    "ko": "kr", "ru": "ru", "es": "sp", "bn": "bn", "fr": "fr",
    "hi": "hi", "id": "id", "it": "it", "pl": "pl", "pt": "pt",
    "ur": "ur", "vi": "vi", "zh": "zh",
}

_GOOGLE_LANG_MAP = {
    "zh": "zh-CN", "ja": "ja", "ko": "ko", "bn": "bn",
    "ur": "ur", "vi": "vi", "hi": "hi", "ar": "ar",
}

# ── Yeni modül isimleri ────────────────────────────────────────────────────────
NEW_TEXT_MODULES = [
    "etkinlik_tavsiye", "spor_aktivite", "kariyer_yolu",
    "insan_kaynaklari", "duygusal_ruhsal", "meditasyon_egzersiz",
]
NEW_DICT_MODULES = [
    "kitap_tavsiye", "film_tavsiye", "muzik_tavsiye",
    "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon", "saglik_tavsiye",
]
ALL_NEW_MODULES = NEW_TEXT_MODULES + NEW_DICT_MODULES

# ── Yardımcı ──────────────────────────────────────────────────────────────────
def call_groq(prompt, max_tokens=600):
    for attempt in range(3):
        try:
            time.sleep(REQUEST_DELAY)
            r = groq_client.chat.completions.create(
                model=MODEL_SMART,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err:
                wait = 45 * (attempt + 1)
                print(f"  Rate limit — {wait}s bekleniyor...")
                time.sleep(wait)
            else:
                print(f"  Groq hata: {e}")
                time.sleep(5)
    return ""

def _parse_json(raw, fallback):
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else fallback
    except Exception:
        return fallback

def _gt(text, lang):
    if not text or not text.strip():
        return text
    mapped = _GOOGLE_LANG_MAP.get(lang, lang)
    SEP = chr(10) + chr(10)
    MAX_CHUNK = 4800
    if len(text) <= MAX_CHUNK:
        try:
            return GoogleTranslator(source="en", target=mapped).translate(text) or text
        except Exception as e:
            print(f"    GT hata: {e}"); return text
    paragraphs = text.split(SEP)
    chunks, cur, cur_len = [], [], 0
    for p in paragraphs:
        if cur_len + len(p) + 2 > MAX_CHUNK and cur:
            chunks.append(SEP.join(cur)); cur, cur_len = [p], len(p)
        else:
            cur.append(p); cur_len += len(p) + 2
    if cur: chunks.append(SEP.join(cur))
    parts = []
    for c in chunks:
        try:
            parts.append(GoogleTranslator(source="en", target=mapped).translate(c) or c)
            time.sleep(0.5)
        except Exception as e:
            print(f"    GT chunk hata: {e}"); parts.append(c)
    return SEP.join(parts)

def _gt_dict(data, lang):
    if isinstance(data, str):   return _gt(data, lang)
    if isinstance(data, dict):  return {k: _gt_dict(v, lang) for k, v in data.items()}
    if isinstance(data, list):  return [_gt_dict(i, lang) for i in data]
    return data

# ── Tip A prompt'ları ─────────────────────────────────────────────────────────
TIP_A_PROMPTS = {
    "etkinlik_tavsiye": lambda t, te: (
        f'Write activity and event recommendations in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🎯 Why These Activities Suit You\n[2 sentences: explain specifically why these activities match the {te} personality]\n\n'
        f'🌟 Top Activities\n• [Activity 1]: [why it suits {te}]\n• [Activity 2]: [why it suits {te}]\n• [Activity 3]: [why it suits {te}]\n\n'
        f'🌿 Outdoor Option\n• [Outdoor activity]: [why it suits {te}]\n\n'
        f'🏠 Indoor Option\n• [Indoor activity]: [why it suits {te}]\n\nKeep it under 120 words. Return ONLY the text.'
    ),
    "spor_aktivite": lambda t, te: (
        f'Write sport and physical activity recommendations in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'💪 Why These Sports Suit You\n[1-2 sentences: explain specifically why these sports match the {te} personality]\n\n'
        f'🏃 Recommended Sports\n• [Sport 1]: [why it fits {te}]\n• [Sport 2]: [why it fits {te}]\n• [Sport 3]: [why it fits {te}]\n\n'
        f'⏱️ Ideal Training Style\n[1-2 sentences]\n\n'
        f'⚠️ Avoid\n[1 exercise type not suited to {te} and why]\n\nKeep it under 100 words. Return ONLY the text.'
    ),
    "kariyer_yolu": lambda t, te: (
        f'Write a career path profile in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🎯 Natural Career Direction\n[2 sentences specific to {te} personality]\n\n'
        f'💼 Best-Fit Roles\n• [Role 1]: [why it suits {te}]\n• [Role 2]: [why it suits {te}]\n• [Role 3]: [why it suits {te}]\n\n'
        f'📈 Growth Strategy\n[2 sentences]\n\n'
        f'⚠️ Environments to Avoid\n[1 environment not suited to {te} and why]\n\nKeep it under 120 words. Return ONLY the text.'
    ),
    "insan_kaynaklari": lambda t, te: (
        f'Write a human resources and teamwork profile in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🤝 Team Dynamic\n[2 sentences about their unique team value specific to {te} personality]\n\n'
        f'💪 HR Strengths\n• [Strength 1 for {te}]\n• [Strength 2 for {te}]\n\n'
        f'📊 Leadership Style\n[1-2 sentences]\n\n'
        f'✅ Collaboration Tips\n• [Tip 1]\n• [Tip 2]\n\nKeep it under 100 words. Return ONLY the text.'
    ),
    "duygusal_ruhsal": lambda t, te: (
        f'Write an emotional and spiritual development profile in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🌱 Emotional Core\n[2 sentences specific to {te} emotional nature]\n\n'
        f'💙 Emotional Strengths\n• [Strength 1]\n• [Strength 2]\n\n'
        f'🔮 Spiritual Path\n[2 sentences about practices resonating with {te} personality]\n\n'
        f'✨ Daily Practice\n[1 specific daily practice perfectly suited to {te} personality]\n\nKeep it under 90 words. Return ONLY the text.'
    ),
    "meditasyon_egzersiz": lambda t, te: (
        f'Write a meditation and mindfulness exercise profile in English for someone with a "{te}" personality. '
        f'Use EXACTLY this format:\n\n'
        f'🧘 Why This Works for You\n[1-2 sentences: specifically why meditation suits {te} personality]\n\n'
        f'🌟 Best Practices\n• [Practice 1]: [why it suits {te}]\n• [Practice 2]: [why it suits {te}]\n\n'
        f'⏰ Timing\n[1 sentence about ideal time and duration for {te}]\n\n'
        f'🌬️ Breathing Technique\n[1 breathing technique suited to {te} and why]\n\nKeep it under 80 words. Return ONLY the text.'
    ),
}

# ── Tip B üretici fonksiyonlar ─────────────────────────────────────────────────
def _gen_kitap(te):
    p = (
        f'Generate book recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why these genres suit {te}",'
        f'"kategoriler": [{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["T by A","T by A","T by A"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["T by A","T by A","T by A"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["T by A","T by A","T by A"]}}],'
        f'"okuma_stili": "how {te} personality engages with books"}}'
    )
    fb = {"neden": f"Books complement the {te} personality.", "kategoriler": [
        {"tur": "Personal Development", "neden": f"Aligns with {te} drive for growth.", "oneriler": ["Atomic Habits by James Clear", "Mindset by Carol Dweck", "The Power of Now by Eckhart Tolle"]},
        {"tur": "Biography", "neden": f"Inspires {te} through real stories.", "oneriler": ["Leonardo da Vinci by Walter Isaacson", "Long Walk to Freedom by Nelson Mandela", "Educated by Tara Westover"]},
        {"tur": "Philosophy", "neden": f"Feeds {te} depth.", "oneriler": ["Meditations by Marcus Aurelius", "Man's Search for Meaning by Viktor Frankl", "The Alchemist by Paulo Coelho"]},
    ], "okuma_stili": f"The {te} personality reads deeply."}
    return _parse_json(call_groq(p, 700), fb)

def _gen_film(te):
    p = (
        f'Generate film recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why these genres appeal to {te}",'
        f'"kategoriler": [{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["Film (Year)","Film (Year)","Film (Year)"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["Film (Year)","Film (Year)","Film (Year)"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "oneriler": ["Film (Year)","Film (Year)","Film (Year)"]}}],'
        f'"izleme_stili": "how {te} personality watches films"}}'
    )
    fb = {"neden": f"Films that reflect depth resonate with {te}.", "kategoriler": [
        {"tur": "Drama", "neden": f"Speaks to {te} emotional depth.", "oneriler": ["The Shawshank Redemption (1994)", "Schindler's List (1993)", "Good Will Hunting (1997)"]},
        {"tur": "Documentary", "neden": f"Feeds {te} need for insight.", "oneriler": ["Free Solo (2018)", "13th (2016)", "Jiro Dreams of Sushi (2011)"]},
        {"tur": "Thriller", "neden": f"Engages {te} analytical mind.", "oneriler": ["Inception (2010)", "Parasite (2019)", "Gone Girl (2014)"]},
    ], "izleme_stili": f"The {te} personality watches attentively."}
    return _parse_json(call_groq(p, 700), fb)

def _gen_muzik(te):
    p = (
        f'Generate music recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why this music suits {te}",'
        f'"turler": [{{"tur": "Genre", "neden": "why it suits {te}", "sanatcilar": ["A1","A2","A3"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "sanatcilar": ["A1","A2","A3"]}},'
        f'{{"tur": "Genre", "neden": "why it suits {te}", "sanatcilar": ["A1","A2","A3"]}}],'
        f'"dinleme_stili": "how {te} personality engages with music"}}'
    )
    fb = {"neden": f"Music channels {te} inner world.", "turler": [
        {"tur": "Classical", "neden": f"Mirrors {te} structured nature.", "sanatcilar": ["Beethoven", "Bach", "Chopin"]},
        {"tur": "Jazz", "neden": f"Matches {te} improvisation.", "sanatcilar": ["Miles Davis", "John Coltrane", "Norah Jones"]},
        {"tur": "Indie", "neden": f"Speaks to {te} authenticity.", "sanatcilar": ["Bon Iver", "Sufjan Stevens", "Phoebe Bridgers"]},
    ], "dinleme_stili": f"The {te} personality listens deeply."}
    return _parse_json(call_groq(p, 600), fb)

def _gen_podcast(te):
    p = (
        f'Generate podcast recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why these podcast categories suit {te}",'
        f'"kategoriler": [{{"tur": "Category", "neden": "why it suits {te}", "oneriler": ["P1","P2","P3"]}},'
        f'{{"tur": "Category", "neden": "why it suits {te}", "oneriler": ["P1","P2","P3"]}},'
        f'{{"tur": "Category", "neden": "why it suits {te}", "oneriler": ["P1","P2","P3"]}}]}}'
    )
    fb = {"neden": f"Podcasts offer {te} meaningful content.", "kategoriler": [
        {"tur": "Personal Development", "neden": f"Supports {te} growth.", "oneriler": ["The Tim Ferriss Show", "Dare to Lead with Brené Brown", "The School of Greatness"]},
        {"tur": "Science & Technology", "neden": f"Feeds {te} curiosity.", "oneriler": ["Lex Fridman Podcast", "Radiolab", "Hidden Brain"]},
        {"tur": "Mindfulness", "neden": f"Grounds {te} inner experience.", "oneriler": ["On Being with Krista Tippett", "10% Happier", "The Daily Meditation Podcast"]},
    ]}
    return _parse_json(call_groq(p, 600), fb)

def _gen_seyahat(te):
    p = (
        f'Generate travel recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why this travel style suits {te}",'
        f'"destinasyon_tipi": ["Type1","Type2","Type3"],'
        f'"aktiviteler": [{{"aktivite": "Activity", "neden": "why it suits {te}"}},{{"aktivite": "Activity", "neden": "why it suits {te}"}},{{"aktivite": "Activity", "neden": "why it suits {te}"}}],'
        f'"seyahat_stili": "how {te} personality travels"}}'
    )
    fb = {"neden": f"Travel enriches {te} through exploration.", "destinasyon_tipi": ["Cultural cities", "Nature retreats", "Historical sites"],
        "aktiviteler": [{"aktivite": "Museum visits", "neden": f"Satisfies {te} curiosity."}, {"aktivite": "Hiking", "neden": f"Gives {te} reflection space."}, {"aktivite": "Local cuisine tours", "neden": f"Connects {te} to authentic experiences."}],
        "seyahat_stili": f"The {te} personality travels with intention."}
    return _parse_json(call_groq(p, 600), fb)

def _gen_afirasyon(te):
    p = (
        f'Generate daily affirmations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences why these affirmations are designed for {te} inner dynamics",'
        f'"sabah": "powerful morning affirmation for {te}",'
        f'"aksam": "grounding evening affirmation for {te}",'
        f'"haftalik": ["Mon affirmation","Tue affirmation","Wed affirmation","Thu affirmation","Fri affirmation","Sat affirmation","Sun affirmation"]}}'
    )
    fb = {"neden": f"These affirmations strengthen {te} personality.",
        "sabah": f"I embrace my {te} nature and move through the day with confidence.",
        "aksam": f"I honor the depth I brought today and release what no longer serves my growth.",
        "haftalik": [f"My {te} spirit leads me toward my highest potential.", "I trust my natural strengths.", "Every challenge sharpens my character.", "I am worthy of all the good.", "My unique perspective creates value.", "I nurture my gifts generously.", "I rest in the knowledge of who I am."]}
    return _parse_json(call_groq(p, 700), fb)

def _gen_saglik(te):
    p = (
        f'Generate structured health recommendations for a "{te}" personality. '
        f'Return ONLY valid JSON: {{"neden": "2 sentences: personality-health connection for {te}",'
        f'"beslenme": {{"tavsiye": "nutrition advice for {te}", "neden": "why it suits {te}"}},'
        f'"hareket": {{"tavsiye": "movement advice for {te}", "neden": "why it suits {te}"}},'
        f'"uyku": {{"tavsiye": "sleep advice for {te}", "neden": "why it suits {te}"}},'
        f'"zihin": {{"tavsiye": "mental health practice for {te}", "neden": "why it suits {te}"}}}}'
    )
    fb = {"neden": f"The {te} personality's health should support vitality and clarity.",
        "beslenme": {"tavsiye": "Prioritize whole foods with regular meal timing.", "neden": f"Supports {te} consistent performance."},
        "hareket": {"tavsiye": "Combine strength training with mindful movement.", "neden": f"Balances {te} active nature with restoration."},
        "uyku": {"tavsiye": "Maintain 7-8 hours with a wind-down ritual.", "neden": f"Helps {te} process rich inner experience."},
        "zihin": {"tavsiye": "Practice daily journaling and social connection.", "neden": f"Gives {te} a healthy outlet for depth."}}
    return _parse_json(call_groq(p, 700), fb)

DICT_GENERATORS = {
    "kitap_tavsiye":    _gen_kitap,
    "film_tavsiye":     _gen_film,
    "muzik_tavsiye":    _gen_muzik,
    "podcast_tavsiye":  _gen_podcast,
    "seyahat_tavsiye":  _gen_seyahat,
    "gunluk_afirasyon": _gen_afirasyon,
    "saglik_tavsiye":   _gen_saglik,
}

# ── İlerleme ───────────────────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f: return json.load(f)
    return {}

def save_progress(p):
    with open(PROGRESS_FILE, "w") as f: json.dump(p, f, ensure_ascii=False, indent=2)

# ── Ana akış ───────────────────────────────────────────────────────────────────
def main():
    progress = load_progress()
    total = len(SIFATLAR)

    for idx, (trait_tr, trait_en) in enumerate(SIFATLAR.items(), 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{total}] {trait_tr} ({trait_en})")
        print(f"{'='*60}")

        # Adım 1: İngilizce yeni modülleri üret (bir kez)
        en_patch_key = f"{trait_tr}::en_patch"
        if en_patch_key in progress:
            print(f"  ✓ EN patch zaten yapılmış")
            en_new = progress[en_patch_key]
        else:
            print(f"  → EN yeni modüller üretiliyor...")
            en_new = {}
            for mod in NEW_TEXT_MODULES:
                print(f"    {mod}...")
                en_new[mod] = call_groq(TIP_A_PROMPTS[mod](trait_tr, trait_en), 500)
            for mod, gen_fn in DICT_GENERATORS.items():
                print(f"    {mod} (dict)...")
                en_new[mod] = gen_fn(trait_en)
            progress[en_patch_key] = en_new
            save_progress(progress)

            # EN koleksiyonuna ekle
            DB["coach_attributes_en"].update_one(
                {"_id": trait_tr},
                {"$set": en_new},
                upsert=False
            )
            print(f"  ✓ EN patch kaydedildi")

        # Adım 2: TR — title/desc koruyarak Google Translate
        tr_patch_key = f"{trait_tr}::tr_patch"
        if tr_patch_key not in progress:
            print(f"  → TR patch Google Translate...")
            tr_new = {}
            for mod in NEW_TEXT_MODULES:
                tr_new[mod] = _gt(en_new.get(mod, ""), "tr")
                time.sleep(0.3)
            for mod in NEW_DICT_MODULES:
                tr_new[mod] = _gt_dict(en_new.get(mod, {}), "tr")
            DB["coach_attributes_tr"].update_one({"_id": trait_tr}, {"$set": tr_new}, upsert=False)
            progress[tr_patch_key] = True
            save_progress(progress)
            print(f"  ✓ TR patch kaydedildi")

        # Adım 3: Diğer 16 dil
        for lang_code, col_suffix in LANGUAGES.items():
            if lang_code in ("en", "tr"):
                continue
            lp_key = f"{trait_tr}::{lang_code}_patch"
            if lp_key in progress:
                print(f"  ✓ {lang_code} zaten")
                continue
            print(f"  → {lang_code} Google Translate...")
            new_fields = {}
            for mod in NEW_TEXT_MODULES:
                new_fields[mod] = _gt(en_new.get(mod, ""), lang_code)
                time.sleep(0.3)
            for mod in NEW_DICT_MODULES:
                new_fields[mod] = _gt_dict(en_new.get(mod, {}), lang_code)
            DB[f"coach_attributes_{col_suffix}"].update_one(
                {"_id": trait_tr}, {"$set": new_fields}, upsert=False
            )
            progress[lp_key] = True
            save_progress(progress)
            print(f"  ✓ {lang_code} kaydedildi")

        print(f"  ✅ {trait_tr} TAMAMLANDI")

    print("\n" + "="*60)
    print("TÜM PATCH'LER TAMAMLANDI")
    print("="*60)
    print("\n📊 Doğrulama (kitap_tavsiye varlığı):")
    for lang_code, col_suffix in LANGUAGES.items():
        col = DB[f"coach_attributes_{col_suffix}"]
        count = col.count_documents({"_id": {"$in": list(SIFATLAR.keys())}, "kitap_tavsiye": {"$exists": True}})
        print(f"  {lang_code}: {count}/21")

if __name__ == "__main__":
    if not GROQ_API_KEY or not MONGO_URI:
        print("HATA: GROQ_API_KEY ve MONGO_URI env değişkenleri gerekli!")
        sys.exit(1)
    main()
