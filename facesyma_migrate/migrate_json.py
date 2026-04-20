"""
migrate_json.py
===============
sifat_veritabani.json (Türkçe) → sifat_veritabani_{lang}.json (17 dil)

Özellikler:
  - Batch çeviri: 10 metin / istek → ~70 dakika tüm diller
  - Akıllı koruma: şarkı adları, film adları korunur
  - Checkpoint: Ctrl+C → --resume ile devam
  - Kuru çalıştırma: --dry-run

KULLANIM:
  pip install deep-translator

  python migrate_json.py                  # Tüm 17 dil
  python migrate_json.py --langs en,de   # 2 dil
  python migrate_json.py --resume        # Devam ettir
  python migrate_json.py --dry-run --langs en  # Test

ÇIKTI:
  sifat_veritabani_en.json
  sifat_veritabani_de.json
  ...
  (uygulama klasörüne kopyalanır)
"""

import os, sys, json, time, re, argparse, logging
from pathlib  import Path
from datetime import datetime
from copy     import deepcopy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("migrate_json.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

# ── Sabitler ─────────────────────────────────────────────────────

SRC_JSON      = Path(__file__).parent / "sifat_veritabani.json"
OUT_DIR       = Path(__file__).parent
PROGRESS_FILE = Path("migrate_json_progress.json")
BATCH_SIZE    = 10
DELAY_SEC     = 0.5
MAX_RETRY     = 3

LANG_MAP = {
    "en": "en",
    "de": "de",
    "ru": "ru",
    "ar": "ar",
    "es": "es",
    "ko": "ko",
    "ja": "ja",
    "zh": "zh-CN",
    "hi": "hi",
    "fr": "fr",
    "pt": "pt",
    "bn": "bn",
    "id": "id",
    "ur": "ur",
    "it": "it",
    "vi": "vi",
    "pl": "pl",
}

# Çevrilmeyecek modüller (dil bağımsız içerik veya özel yapı)
# astroloji ayrı işlenir (burç adları)
SKIP_MODULES = set()

# Korunacak pattern'ler — bunlar placeholder'a dönüştürülüp geri konur
# Sanatçı adları, film/dizi isimleri, teori isimleri, parantez içi Türkçe olmayan
PROTECT_PATTERNS = [
    # Şarkı/sanatçı: "İsim – Sanatçı" satırları
    (r'•\s+([^\n–]+)\s+–\s+([^\n]+)', '__BULLET__{idx}__'),
    # Parantez içi yıl: (2016, Film) (Dizi) (Kısa belgesel)
    (r'\((\d{4})[^)]*\)', '__YEAR__{idx}__'),
    # Teori isimleri: (Hambrick & Mason (1984)...)
    (r'\(([A-Z][^)]+\d{4}[^)]*)\)', '__THEORY__{idx}__'),
    # Big Five / Hogan / STAR / 360
    (r'(Big Five|Hogan HPI|Hogan HDS|Hogan MVPI|HEXACO|MBTI|STAR|360|OCEAN)',
     '__TERM__{idx}__'),
]

# ── Placeholder sistemi ───────────────────────────────────────────

def protect_text(text: str) -> tuple[str, dict]:
    """
    Korunacak kısımları placeholder'larla değiştirir.
    Returns: (işlenmiş_metin, {placeholder: orijinal})
    """
    protected = {}
    result    = text
    counter   = [0]

    # Bullet satırlarını koru (şarkı/film isimleri)
    lines_out = []
    for line in result.split('\n'):
        # • Başlıklı satırlar: içeriği koru ama satırı çevir
        if line.strip().startswith('•') and '–' in line:
            # Sol taraf (isim) koru, sağ taraf (açıklama) çevir
            parts = line.split('–', 1)
            left  = parts[0]  # • Film Adı
            right = parts[1] if len(parts) > 1 else ''
            key   = f'__PROT_{counter[0]}__'
            protected[key] = left
            counter[0] += 1
            lines_out.append(f'{key} – {right}')
        else:
            lines_out.append(line)
    result = '\n'.join(lines_out)

    # Özel terimleri koru — en uzundan başla (overlap önleme)
    PROTECT_TERMS = [
        'Big Five', 'Hogan HPI', 'Hogan HDS', 'Hogan MVPI',
        'HEXACO', 'MBTI', 'STAR metodu', 'AutoML',
        'Hambrick', 'Blanchard', 'Hersey', 'McCrae', 'Costa',
        'Gross', 'Vroom', 'Maslow', 'McGregor',
    ]
    for term in sorted(PROTECT_TERMS, key=len, reverse=True):
        if term in result:
            key = f'__PROT_{counter[0]}__'
            protected[key] = term
            result = result.replace(term, key)  # tüm geçişleri değiştir
            counter[0] += 1

    return result, protected


def restore_text(text: str, protected: dict) -> str:
    """Placeholder'ları orijinal değerlerle geri koy."""
    result = text
    for key, val in protected.items():
        result = result.replace(key, val)
    return result


# ── Çevirmen ─────────────────────────────────────────────────────

def translate_batch(texts: list, target: str) -> list:
    """Batch çeviri — rate limit korumalı."""
    from deep_translator import GoogleTranslator
    results = []

    for i in range(0, len(texts), BATCH_SIZE):
        chunk = texts[i:i + BATCH_SIZE]
        for attempt in range(1, MAX_RETRY + 1):
            try:
                translated = GoogleTranslator(source='tr', target=target).translate_batch(chunk)
                results.extend(t if t else chunk[j] for j, t in enumerate(translated))
                break
            except Exception as e:
                wait = attempt * 2
                log.warning(f"  Çeviri hatası (deneme {attempt}/{MAX_RETRY}): {e}")
                if attempt < MAX_RETRY:
                    time.sleep(wait)
                else:
                    log.error("  Başarısız — orijinal kullanılıyor")
                    results.extend(chunk)
        time.sleep(DELAY_SEC)

    return results


def translate_field(text: str, target: str) -> str:
    """Tek alan çeviri — korumalı."""
    if not text or not text.strip():
        return text

    protected_text, prot_map = protect_text(text)
    translated_list = translate_batch([protected_text], target)
    translated      = translated_list[0] if translated_list else protected_text
    return restore_text(translated, prot_map)


# ── İlerleme ─────────────────────────────────────────────────────

def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_progress(progress: dict):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)


# ── Ana migration ─────────────────────────────────────────────────

def migrate_lang(data: dict, lang_code: str, gt_code: str,
                 progress: dict, dry_run: bool) -> dict:
    """
    Tek bir dil için tüm sıfat veritabanını çevirir.
    Returns: çevrilmiş data dict
    """
    translated_data = {}
    modules = [
        'tavsiye', 'motivasyon', 'astroloji', 'etkinlik',
        'muzik', 'film_dizi', 'kariyer', 'giyim',
        'liderlik', 'duygusal', 'uyum', 'beceri', 'ik'
    ]

    total     = len(data)
    done_keys = set(progress.get(lang_code, {}).keys())

    for idx, (sifat, fields) in enumerate(data.items(), 1):
        translated_fields = {}

        for mod in modules:
            val = fields.get(mod, '')
            if not val:
                translated_fields[mod] = val
                continue

            prog_key = f"{sifat}:{mod}"
            if prog_key in done_keys:
                # Önceden çevrilmiş — progress'ten yükle
                cached = progress.get(lang_code, {}).get(prog_key)
                translated_fields[mod] = cached if cached else val
                continue

            log.info(f"  [{idx:3d}/{total}] {sifat[:35]:<35} [{mod}]")

            if dry_run:
                translated_fields[mod] = f"[{gt_code.upper()}: {str(val)[:40]}...]"
            else:
                translated_fields[mod] = translate_field(str(val), gt_code)

            # İlerlemeyi kaydet
            if lang_code not in progress:
                progress[lang_code] = {}
            progress[lang_code][prog_key] = translated_fields[mod]
            save_progress(progress)

        translated_data[sifat] = translated_fields

    return translated_data


def migrate(langs: list, dry_run: bool, resume: bool):
    t0 = datetime.now()

    # JSON yükle
    if not SRC_JSON.exists():
        log.error(f"Kaynak JSON bulunamadı: {SRC_JSON}")
        sys.exit(1)

    with open(SRC_JSON, encoding='utf-8') as f:
        data = json.load(f)

    log.info(f"Kaynak JSON: {len(data)} sıfat, {len(list(data.values())[0])} modül")

    # İlerleme yükle
    progress = load_progress() if resume else {}
    if resume and progress:
        done_count = sum(len(v) for v in progress.values())
        log.info(f"Devam ediliyor — {done_count} alan tamamlanmış")

    for lang_code in langs:
        gt_code = LANG_MAP[lang_code]
        out_path = OUT_DIR / f"sifat_veritabani_{lang_code}.json"

        log.info(f"\n{'='*55}")
        log.info(f"DİL: {lang_code.upper()} ({gt_code})  →  {out_path.name}")
        log.info(f"{'='*55}")

        # Mevcut dosya varsa ve resume ise yükle
        existing = {}
        if resume and out_path.exists():
            with open(out_path, encoding='utf-8') as f:
                existing = json.load(f)
            log.info(f"  Mevcut dosya yüklendi: {len(existing)} sıfat")

        translated = migrate_lang(data, lang_code, gt_code, progress, dry_run)

        # Mevcut ile birleştir (resume için)
        if existing:
            existing.update(translated)
            translated = existing

        if not dry_run:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(translated, f, ensure_ascii=False, indent=2)
            log.info(f"  Kaydedildi: {out_path}")
        else:
            log.info(f"  DRY RUN — {out_path.name} yazılmadı")

        # Facesyma revize klasörüne kopyala
        if not dry_run:
            dest = Path(__file__).parent.parent / "facesyma_revize" / out_path.name
            if dest.parent.exists():
                import shutil
                shutil.copy2(out_path, dest)
                log.info(f"  Kopyalandı: {dest}")

    elapsed = (datetime.now() - t0).total_seconds()
    log.info(f"\n{'='*55}")
    log.info(f"TAMAMLANDI: {elapsed:.0f}s ({elapsed/60:.1f} dk)")
    log.info(f"Diller: {', '.join(langs)}")
    if dry_run:
        log.info("NOT: Dry run — dosyalar yazılmadı.")
    log.info(f"{'='*55}")

    if not dry_run and PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()


# ── CLI ───────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="sifat_veritabani.json → 17 dil JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python migrate_json.py                    # Tüm 7 dil (~70 dk)
  python migrate_json.py --langs en         # Sadece İngilizce (~10 dk)
  python migrate_json.py --langs en,de,ru   # 3 dil (~30 dk)
  python migrate_json.py --resume           # Devam ettir
  python migrate_json.py --dry-run --langs en  # Test
        """
    )
    p.add_argument("--langs",   default=",".join(LANG_MAP))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume",  action="store_true")
    p.add_argument("--delay",   type=float, default=DELAY_SEC)
    p.add_argument("--src",     default=str(SRC_JSON))
    args = p.parse_args()

    global DELAY_SEC, SRC_JSON
    DELAY_SEC = args.delay
    SRC_JSON  = Path(args.src)

    langs   = [l.strip() for l in args.langs.split(",") if l.strip() in LANG_MAP]
    unknown = [l.strip() for l in args.langs.split(",") if l.strip() not in LANG_MAP]
    if unknown:
        print(f"HATA: Bilinmeyen dil → {unknown}")
        sys.exit(1)

    with open(SRC_JSON, encoding='utf-8') as f:
        data = json.load(f)

    n_sifat  = len(data)
    n_modul  = len(list(data.values())[0])
    n_alan   = n_sifat * n_modul * len(langs)
    est_min  = (n_alan / BATCH_SIZE) * DELAY_SEC / 60

    total_chars = sum(len(str(v)) for d in data.values() for v in d.values())

    print(f"""
╔══════════════════════════════════════════════╗
║     sifat_veritabani.json → Çok Dilli JSON   ║
╚══════════════════════════════════════════════╝

  Kaynak      : {SRC_JSON.name}
  Sıfat sayısı: {n_sifat}
  Modül sayısı: {n_modul}
  Hedef diller: {', '.join(langs)}
  Toplam alan : {n_alan:,}
  Kaynak boyut: {total_chars/1024:.0f} KB × {len(langs)} dil

  Tahmini süre: ~{est_min:.0f} dakika
  Dry run     : {args.dry_run}
  Resume      : {args.resume}

  Çıktı dosyaları:
{chr(10).join(f"    sifat_veritabani_{l}.json" for l in langs)}
""")

    cevap = input("Başlansın mı? (e/h): ").strip().lower()
    if cevap not in ("e", "evet", "y", "yes"):
        print("İptal.")
        sys.exit(0)

    try:
        migrate(langs=langs, dry_run=args.dry_run, resume=args.resume)
    except KeyboardInterrupt:
        log.warning("\nDurduruldu. --resume ile devam edebilirsiniz.")
        sys.exit(0)


if __name__ == "__main__":
    main()
