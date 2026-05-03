"""
patch_new_modules.py  (paralel versiyon)
=========================================
Mevcut 21 sıfat dökümanlarına 13 yeni modülü ekler.
Google Translate çevirileri ThreadPoolExecutor ile paralel çalışır:
  - Her sıfat için TR + 16 dil aynı anda çevrilir
  - Her dil içinde 13 modül paralel çevrilir
  → Sequential'a göre ~10x hızlı

Çalıştırma:
  pip install deep-translator
  python patch_new_modules.py

İlerleme: c:/tmp/patch_progress.json  (kesintide devam eder)
"""

import os, json, time, re, sys, threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
from groq import Groq

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("HATA: pip install deep-translator")
    sys.exit(1)

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
MONGO_URI     = os.environ.get("MONGO_URI", "")
_TMP          = "c:/tmp" if os.name == "nt" else "/tmp"
os.makedirs(_TMP, exist_ok=True)
PROGRESS_FILE = f"{_TMP}/patch_progress.json"
MODEL_SMART   = "llama-3.3-70b-versatile"
MODEL_FAST    = "llama-3.1-8b-instant"
REQUEST_DELAY = 2.0
GT_WORKERS    = 8   # paralel GT thread sayısı (dil başına modül çevirisi)
LANG_WORKERS  = 6   # paralel dil sayısı (aynı anda kaç dil çevrilsin)

groq_client  = Groq(api_key=GROQ_API_KEY)
mongo_client = MongoClient(MONGO_URI)
DB           = mongo_client["facesyma-coach-backup"]

# GT isteklerini throttle etmek için semaphore
_gt_sem = threading.Semaphore(10)
# progress dosyası için lock
_progress_lock = threading.Lock()

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

NEW_TEXT_MODULES = [
    "etkinlik_tavsiye", "spor_aktivite", "kariyer_yolu",
    "insan_kaynaklari", "duygusal_ruhsal", "meditasyon_egzersiz",
]
NEW_DICT_MODULES = [
    "kitap_tavsiye", "film_tavsiye", "muzik_tavsiye",
    "podcast_tavsiye", "seyahat_tavsiye", "gunluk_afirasyon", "saglik_tavsiye",
]

# ── Groq ──────────────────────────────────────────────────────────────────────
def call_groq(prompt, max_tokens=600, model=None):
    use_model = model or MODEL_SMART
    for attempt in range(5):
        try:
            time.sleep(REQUEST_DELAY)
            r = groq_client.chat.completions.create(
                model=use_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err:
                wait = 30 * (attempt + 1)
                print(f"  Rate limit — {wait}s bekleniyor...")
                time.sleep(wait)
            else:
                print(f"  Groq hata: {e}")
                time.sleep(5)
    print(f"  UYARI: 5 denemede başarısız, boş döndürülüyor")
    return ""

def _parse_json(raw, fallback):
    try:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group()) if m else fallback
    except Exception:
        return fallback

# ── Google Translate (thread-safe) ────────────────────────────────────────────
def _gt(text, lang):
    if not text or not text.strip():
        return text
    mapped = _GOOGLE_LANG_MAP.get(lang, lang)
    SEP = chr(10) + chr(10)
    MAX_CHUNK = 4800

    with _gt_sem:
        if len(text) <= MAX_CHUNK:
            try:
                return GoogleTranslator(source="en", target=mapped).translate(text) or text
            except Exception as e:
                print(f"    GT hata ({lang}): {e}")
                return text

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
                time.sleep(0.2)
            except Exception as e:
                print(f"    GT chunk hata: {e}"); parts.append(c)
        return SEP.join(parts)


def _gt_dict(data, lang):
    if isinstance(data, str):  return _gt(data, lang)
    if isinstance(data, dict): return {k: _gt_dict(v, lang) for k, v in data.items()}
    if isinstance(data, list): return [_gt_dict(i, lang) for i in data]
    return data


def translate_all_parallel(en_new, lang_code):
    """Bir dil için 13 modülü paralel çevirir."""
    results = {}

    def do_text(mod):
        return mod, _gt(en_new.get(mod, ""), lang_code)

    def do_dict(mod):
        return mod, _gt_dict(en_new.get(mod, {}), lang_code)

    with ThreadPoolExecutor(max_workers=GT_WORKERS) as pool:
        futures = {}
        for mod in NEW_TEXT_MODULES:
            futures[pool.submit(do_text, mod)] = mod
        for mod in NEW_DICT_MODULES:
            futures[pool.submit(do_dict, mod)] = mod

        for f in as_completed(futures):
            try:
                mod, val = f.result()
                results[mod] = val
            except Exception as e:
                mod = futures[f]
                print(f"    {lang_code}/{mod} hata: {e}")

    return results

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
    p = (f'Generate book recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why these genres suit {te}","kategoriler":[{{"tur":"Genre","neden":"why it suits {te}","oneriler":["T by A","T by A","T by A"]}},{{"tur":"Genre","neden":"why it suits {te}","oneriler":["T by A","T by A","T by A"]}},{{"tur":"Genre","neden":"why it suits {te}","oneriler":["T by A","T by A","T by A"]}}],"okuma_stili":"how {te} reads"}}')
    fb = {"neden": f"Books complement {te}.", "kategoriler": [
        {"tur": "Personal Development", "neden": f"Aligns with {te} growth.", "oneriler": ["Atomic Habits by James Clear", "Mindset by Carol Dweck", "The Power of Now by Eckhart Tolle"]},
        {"tur": "Biography", "neden": f"Inspires {te}.", "oneriler": ["Leonardo da Vinci by Walter Isaacson", "Long Walk to Freedom by Nelson Mandela", "Educated by Tara Westover"]},
        {"tur": "Philosophy", "neden": f"Feeds {te} depth.", "oneriler": ["Meditations by Marcus Aurelius", "Man's Search for Meaning by Viktor Frankl", "The Alchemist by Paulo Coelho"]},
    ], "okuma_stili": f"The {te} personality reads deeply."}
    return _parse_json(call_groq(p, 700, MODEL_FAST), fb)

def _gen_film(te):
    p = (f'Generate film recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why these genres appeal to {te}","kategoriler":[{{"tur":"Genre","neden":"why it suits {te}","oneriler":["Film (Year)","Film (Year)","Film (Year)"]}},{{"tur":"Genre","neden":"why it suits {te}","oneriler":["Film (Year)","Film (Year)","Film (Year)"]}},{{"tur":"Genre","neden":"why it suits {te}","oneriler":["Film (Year)","Film (Year)","Film (Year)"]}}],"izleme_stili":"how {te} watches films"}}')
    fb = {"neden": f"Films reflecting depth resonate with {te}.", "kategoriler": [
        {"tur": "Drama", "neden": f"Speaks to {te} depth.", "oneriler": ["The Shawshank Redemption (1994)", "Schindler's List (1993)", "Good Will Hunting (1997)"]},
        {"tur": "Documentary", "neden": f"Feeds {te} insight.", "oneriler": ["Free Solo (2018)", "13th (2016)", "Jiro Dreams of Sushi (2011)"]},
        {"tur": "Thriller", "neden": f"Engages {te} mind.", "oneriler": ["Inception (2010)", "Parasite (2019)", "Gone Girl (2014)"]},
    ], "izleme_stili": f"The {te} personality watches attentively."}
    return _parse_json(call_groq(p, 700, MODEL_FAST), fb)

def _gen_muzik(te):
    p = (f'Generate music recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why this music suits {te}","turler":[{{"tur":"Genre","neden":"why it suits {te}","sanatcilar":["A1","A2","A3"]}},{{"tur":"Genre","neden":"why it suits {te}","sanatcilar":["A1","A2","A3"]}},{{"tur":"Genre","neden":"why it suits {te}","sanatcilar":["A1","A2","A3"]}}],"dinleme_stili":"how {te} engages with music"}}')
    fb = {"neden": f"Music channels {te} inner world.", "turler": [
        {"tur": "Classical", "neden": f"Mirrors {te} structure.", "sanatcilar": ["Beethoven", "Bach", "Chopin"]},
        {"tur": "Jazz", "neden": f"Matches {te} improvisation.", "sanatcilar": ["Miles Davis", "Coltrane", "Norah Jones"]},
        {"tur": "Indie", "neden": f"Speaks to {te} authenticity.", "sanatcilar": ["Bon Iver", "Sufjan Stevens", "Phoebe Bridgers"]},
    ], "dinleme_stili": f"The {te} personality listens deeply."}
    return _parse_json(call_groq(p, 600, MODEL_FAST), fb)

def _gen_podcast(te):
    p = (f'Generate podcast recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why these categories suit {te}","kategoriler":[{{"tur":"Category","neden":"why it suits {te}","oneriler":["P1","P2","P3"]}},{{"tur":"Category","neden":"why it suits {te}","oneriler":["P1","P2","P3"]}},{{"tur":"Category","neden":"why it suits {te}","oneriler":["P1","P2","P3"]}}]}}')
    fb = {"neden": f"Podcasts offer {te} meaningful growth content.", "kategoriler": [
        {"tur": "Personal Development", "neden": f"Supports {te} growth.", "oneriler": ["The Tim Ferriss Show", "Dare to Lead", "The School of Greatness"]},
        {"tur": "Science", "neden": f"Feeds {te} curiosity.", "oneriler": ["Lex Fridman Podcast", "Radiolab", "Hidden Brain"]},
        {"tur": "Mindfulness", "neden": f"Grounds {te}.", "oneriler": ["On Being with Krista Tippett", "10% Happier", "The Daily Meditation Podcast"]},
    ]}
    return _parse_json(call_groq(p, 600, MODEL_FAST), fb)

def _gen_seyahat(te):
    p = (f'Generate travel recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why this travel style suits {te}","destinasyon_tipi":["Type1","Type2","Type3"],'
         f'"aktiviteler":[{{"aktivite":"Activity","neden":"why it suits {te}"}},{{"aktivite":"Activity","neden":"why it suits {te}"}},{{"aktivite":"Activity","neden":"why it suits {te}"}}],"seyahat_stili":"how {te} travels"}}')
    fb = {"neden": f"Travel enriches {te} through exploration.", "destinasyon_tipi": ["Cultural cities", "Nature retreats", "Historical sites"],
        "aktiviteler": [{"aktivite": "Museum visits", "neden": f"Satisfies {te} curiosity."}, {"aktivite": "Hiking", "neden": f"Gives {te} reflection space."}, {"aktivite": "Local cuisine", "neden": f"Connects {te} authentically."}],
        "seyahat_stili": f"The {te} personality travels with intention."}
    return _parse_json(call_groq(p, 600, MODEL_FAST), fb)

def _gen_afirasyon(te):
    p = (f'Generate daily affirmations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences why these affirmations suit {te}","sabah":"morning affirmation for {te}","aksam":"evening affirmation for {te}",'
         f'"haftalik":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}}')
    fb = {"neden": f"These affirmations strengthen {te}.",
        "sabah": f"I embrace my {te} nature and move with confidence.",
        "aksam": f"I honor the depth I brought today.",
        "haftalik": [f"My {te} spirit leads me forward.", "I trust my strengths.", "Challenges sharpen me.", "I am worthy.", "My perspective creates value.", "I nurture my gifts.", "I rest in who I am."]}
    return _parse_json(call_groq(p, 700, MODEL_FAST), fb)

def _gen_saglik(te):
    p = (f'Generate structured health recommendations for a "{te}" personality. Return ONLY valid JSON: '
         f'{{"neden":"2 sentences personality-health connection for {te}",'
         f'"beslenme":{{"tavsiye":"nutrition advice","neden":"why it suits {te}"}},'
         f'"hareket":{{"tavsiye":"movement advice","neden":"why it suits {te}"}},'
         f'"uyku":{{"tavsiye":"sleep advice","neden":"why it suits {te}"}},'
         f'"zihin":{{"tavsiye":"mental practice","neden":"why it suits {te}"}}}}')
    fb = {"neden": f"The {te} personality's health supports vitality.",
        "beslenme": {"tavsiye": "Whole foods with regular timing.", "neden": f"Supports {te} performance."},
        "hareket": {"tavsiye": "Strength + mindful movement.", "neden": f"Balances {te} energy."},
        "uyku": {"tavsiye": "7-8 hours with wind-down ritual.", "neden": f"Helps {te} process deeply."},
        "zihin": {"tavsiye": "Journaling + social connection.", "neden": f"Healthy outlet for {te} depth."}}
    return _parse_json(call_groq(p, 700, MODEL_FAST), fb)

DICT_GENERATORS = {
    "kitap_tavsiye": _gen_kitap, "film_tavsiye": _gen_film,
    "muzik_tavsiye": _gen_muzik, "podcast_tavsiye": _gen_podcast,
    "seyahat_tavsiye": _gen_seyahat, "gunluk_afirasyon": _gen_afirasyon,
    "saglik_tavsiye": _gen_saglik,
}

# ── İlerleme (thread-safe) ────────────────────────────────────────────────────
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f: return json.load(f)
    return {}

def save_progress(p):
    with _progress_lock:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(p, f, ensure_ascii=False, indent=2)

# ── Tek dil işleme (thread'de çağrılır) ──────────────────────────────────────
def process_lang(trait_tr, lang_code, col_suffix, en_new, progress):
    lp_key = f"{trait_tr}::{lang_code}_patch"
    if lp_key in progress:
        return lang_code, "skip"
    try:
        fields = translate_all_parallel(en_new, lang_code)
        DB[f"coach_attributes_{col_suffix}"].update_one(
            {"_id": trait_tr}, {"$set": fields}, upsert=False
        )
        progress[lp_key] = True
        save_progress(progress)
        return lang_code, "ok"
    except Exception as e:
        return lang_code, f"hata: {e}"

# ── Ana akış ──────────────────────────────────────────────────────────────────
def main():
    progress = load_progress()
    total    = len(SIFATLAR)

    for idx, (trait_tr, trait_en) in enumerate(SIFATLAR.items(), 1):
        print(f"\n{'='*55}")
        print(f"[{idx}/{total}] {trait_tr} ({trait_en})")
        print(f"{'='*55}")

        # Adım 1: İngilizce üretim (Groq — sequential, rate limit yüzünden)
        en_key = f"{trait_tr}::en_patch"
        if en_key in progress:
            print(f"  ✓ EN zaten hazır")
            en_new = progress[en_key]
        else:
            print(f"  → EN modüller üretiliyor (Groq)...")
            en_new = {}
            for mod in NEW_TEXT_MODULES:
                print(f"    {mod}...")
                en_new[mod] = call_groq(TIP_A_PROMPTS[mod](trait_tr, trait_en), 500)
            for mod, gen_fn in DICT_GENERATORS.items():
                print(f"    {mod} (dict)...")
                en_new[mod] = gen_fn(trait_en)
            progress[en_key] = en_new
            save_progress(progress)
            DB["coach_attributes_en"].update_one(
                {"_id": trait_tr}, {"$set": en_new}, upsert=False
            )
            print(f"  ✓ EN kaydedildi")

        # Adım 2+3: TR + 16 dil — PARALEL Google Translate
        langs_to_do = [
            (lc, cs) for lc, cs in LANGUAGES.items()
            if lc != "en" and f"{trait_tr}::{lc}_patch" not in progress
        ]

        if not langs_to_do:
            print(f"  ✓ Tüm diller zaten tamamlanmış")
        else:
            print(f"  → {len(langs_to_do)} dil paralel çeviriliyor...")
            with ThreadPoolExecutor(max_workers=LANG_WORKERS) as pool:
                futures = {
                    pool.submit(process_lang, trait_tr, lc, cs, en_new, progress): lc
                    for lc, cs in langs_to_do
                }
                for f in as_completed(futures):
                    lang_code, result = f.result()
                    icon = "✓" if result in ("ok", "skip") else "✗"
                    print(f"    {icon} {lang_code}: {result}")

        print(f"  ✅ {trait_tr} TAMAMLANDI")

    print("\n" + "="*55)
    print("TÜM PATCH'LER TAMAMLANDI")
    print("="*55)

    print("\n📊 Doğrulama (kitap_tavsiye varlığı):")
    for lc, cs in LANGUAGES.items():
        col   = DB[f"coach_attributes_{cs}"]
        count = col.count_documents({"_id": {"$in": list(SIFATLAR.keys())}, "kitap_tavsiye": {"$exists": True}})
        print(f"  {lc}: {count}/21")

if __name__ == "__main__":
    if not GROQ_API_KEY or not MONGO_URI:
        print("HATA: GROQ_API_KEY ve MONGO_URI gerekli!")
        sys.exit(1)
    main()
