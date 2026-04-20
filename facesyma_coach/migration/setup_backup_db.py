"""
facesyma_coach/migration/setup_backup_db.py
============================================
Backup veritabanı kurulumu ve index'leri.

Backup DB: facesyma-coach-backup
  Mevcut facesyma-backend DB'ye hiç dokunmaz.

Koleksiyon yapısı:
  coach_attributes_{lang}   — 201 sıfat × 27 modül (13 eski + 14 yeni)
  coach_users               — Kullanıcının ek yaşam koçu profili
  coach_birth_data          — Doğum tarihi/saati/astroloji cache
  coach_sessions            — Koç oturum geçmişi

Kullanım:
  python setup_backup_db.py --create-indexes
  python setup_backup_db.py --migrate --lang tr
  python setup_backup_db.py --migrate --all-langs
  python setup_backup_db.py --verify
"""

import os, json, argparse, sys
from datetime import datetime
from pathlib  import Path

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
    MONGO_OK = True
except ImportError:
    MONGO_OK = False
    print("UYARI: pymongo yok — pip install pymongo")


MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://facesyma:FaceSyma2021@cluster0.io98c.mongodb.net/"
    "myFirstDatabase?ssl=true&ssl_cert_reqs=CERT_NONE"
)

# Backup DB adı — ASLA mevcut DB ile aynı olmamalı
BACKUP_DB  = "facesyma-coach-backup"
SOURCE_DB  = "facesyma-backend"        # okunur ama yazılmaz

ALL_LANGS  = ["tr","en","de","ru","ar","es","ko","ja",
              "zh","hi","fr","pt","bn","id","ur","it","vi","pl"]

# 14 yeni modül
COACH_MODULES = [
    "saglik_esenwlik", "dogruluk_sadakat", "guvenlik", "suc_egilim",
    "iliski_yonetimi", "iletisim_becerileri", "stres_yonetimi", "ozguven",
    "zaman_yonetimi", "kisisel_hedefler", "astroloji_harita", "dogum_analizi",
    "yas_koc_ozet", "vucut_dil",
]

# Mevcut 13 modül
EXISTING_MODULES = [
    "kariyer", "giyim", "liderlik", "duygusal", "uyum", "beceri",
    "ik", "tavsiye", "motivasyon", "astroloji", "etkinlik", "muzik", "film_dizi",
]

ALL_MODULES = EXISTING_MODULES + COACH_MODULES


def get_backup_db():
    if not MONGO_OK:
        raise RuntimeError("pymongo kurulu değil")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    return client[BACKUP_DB]


def create_indexes(db):
    """Her koleksiyon için gerekli index'leri oluştur."""
    print("Index'ler oluşturuluyor...")

    # 1. coach_attributes_{lang} — sıfat araması
    for lang in ALL_LANGS:
        col = db[f"coach_attributes_{lang}"]
        col.create_index([("_id", ASCENDING)])                          # sıfat adı
        col.create_index([("$**", TEXT)], name="fulltext_search")       # tam metin arama
        print(f"  coach_attributes_{lang} ✓")

    # 2. coach_users — kullanıcı koçluk profili
    col = db["coach_users"]
    col.create_index([("user_id",    ASCENDING)], unique=True)
    col.create_index([("birth_date", ASCENDING)])
    col.create_index([("lang",       ASCENDING)])
    col.create_index([("updated_at", DESCENDING)])
    print("  coach_users ✓")

    # 3. coach_birth_data — astroloji cache
    col = db["coach_birth_data"]
    col.create_index([("user_id",    ASCENDING)], unique=True)
    col.create_index([("birth_date", ASCENDING)])
    col.create_index([("sun_sign",   ASCENDING)])
    print("  coach_birth_data ✓")

    # 4. coach_sessions — koç oturumları
    col = db["coach_sessions"]
    col.create_index([("user_id",    ASCENDING)])
    col.create_index([("session_date", DESCENDING)])
    col.create_index([("module",     ASCENDING)])
    print("  coach_sessions ✓")

    # 5. coach_goals — kişisel hedef takibi
    col = db["coach_goals"]
    col.create_index([("user_id",  ASCENDING)])
    col.create_index([("status",   ASCENDING)])
    col.create_index([("due_date", ASCENDING)])
    print("  coach_goals ✓")

    print("\nTüm index'ler oluşturuldu ✓")


def migrate_lang(lang: str, db, source_dir: Path):
    """
    Üretilen sifat_coach_{lang}.json dosyasını backup DB'ye yazar.
    """
    from pymongo import UpdateOne

    source_file = source_dir / f"sifat_coach_{lang}.json"
    if not source_file.exists():
        print(f"  {lang}: {source_file} bulunamadı — atlanıyor")
        return 0

    with open(source_file, encoding="utf-8") as f:
        data = json.load(f)

    col = db[f"coach_attributes_{lang}"]
    ops = [
        UpdateOne(
            {"_id": sifat},
            {"$set": {
                **entry,
                "_id":        sifat,
                "lang":       lang,
                "updated_at": datetime.now().isoformat(),
                "version":    2,   # v1 = eski modüller, v2 = + koç modülleri
            }},
            upsert=True,
        )
        for sifat, entry in data.items()
    ]

    if ops:
        result = col.bulk_write(ops)
        count = result.upserted_count + result.modified_count
        print(f"  {lang}: {count} kayıt yazıldı → {BACKUP_DB}.coach_attributes_{lang}")
        return count
    return 0


def verify(db):
    """Backup DB içeriğini doğrula."""
    print(f"\nBackup DB: {BACKUP_DB}")
    print("─" * 50)

    cols = db.list_collection_names()
    for col_name in sorted(cols):
        col   = db[col_name]
        count = col.count_documents({})

        # Modül kontrolü
        if col_name.startswith("coach_attributes_"):
            sample = col.find_one()
            if sample:
                present  = [m for m in ALL_MODULES if m in sample]
                missing  = [m for m in ALL_MODULES if m not in sample]
                coach_ok = [m for m in COACH_MODULES if m in sample]
                print(f"  {col_name:35s} {count:4d} kayıt | "
                      f"modül: {len(present)}/27 | "
                      f"koç: {len(coach_ok)}/14 "
                      f"{'✓' if len(missing)==0 else f'⚠ eksik: {missing[:3]}'}")
            else:
                print(f"  {col_name:35s} {count:4d} kayıt (boş)")
        else:
            print(f"  {col_name:35s} {count:4d} kayıt")

    # Kaynak DB ile karşılaştır
    try:
        from pymongo import MongoClient
        client  = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        src_db  = client[SOURCE_DB]
        src_col = src_db["database_attribute_tr"]
        src_count = src_col.count_documents({})
        print(f"\nKaynak DB ({SOURCE_DB}.database_attribute_tr): {src_count} kayıt")
        print("Kaynak DB'ye yazılmadı ✓ — sadece okundu")
    except Exception as e:
        print(f"Kaynak DB kontrolü atlandı: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Kullanıcı koçluk profili şeması
# ─────────────────────────────────────────────────────────────────────────────
COACH_USER_SCHEMA = {
    "_id":              "ObjectId",
    "user_id":          "int — facesyma-backend.appfaceapi_myuser._id",
    "lang":             "str — dil kodu",
    "birth_date":       "YYYY-MM-DD",
    "birth_time":       "HH:MM (opsiyonel)",
    "birth_city":       "str (opsiyonel — astroloji için)",
    "birth_timezone":   "str — örn: Europe/Istanbul",

    # Analiz sonucundan gelen dominant sıfatlar
    "dominant_sifatlar": ["sıfat_1", "sıfat_2", "..."],

    # Hesaplanan koç modülleri (kullanıcıya özel)
    "saglik_skoru":      "0-100",
    "ilişki_stili":      "str",
    "iletisim_tipi":     "str",
    "stres_seviyesi":    "düşük|orta|yüksek",
    "zaman_stili":       "str",
    "ozguven_skoru":     "0-100",

    # Astroloji
    "sun_sign":          "str",
    "moon_sign":         "str (doğum saati gerekli)",
    "ascendant":         "str (doğum saati + şehir gerekli)",
    "life_path_number":  "int (numeroloji)",

    # Hedefler
    "aktif_hedefler":    ["ObjectId"],
    "tamamlanan_hedefler": ["ObjectId"],

    # Meta
    "created_at":        "ISO datetime",
    "updated_at":        "ISO datetime",
    "coach_session_count": "int",
}


def print_schema():
    print("\nKullanıcı Koçluk Profili Şeması (coach_users):")
    print(json.dumps(COACH_USER_SCHEMA, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Backup DB kurulum ve migrasyon")
    p.add_argument("--create-indexes", action="store_true")
    p.add_argument("--migrate",        action="store_true")
    p.add_argument("--all-langs",      action="store_true")
    p.add_argument("--lang",           default="tr")
    p.add_argument("--verify",         action="store_true")
    p.add_argument("--schema",         action="store_true")
    p.add_argument("--source-dir",     default=".",
                   help="sifat_coach_*.json dosyalarının bulunduğu dizin")
    args = p.parse_args()

    if args.schema:
        print_schema(); return

    if not MONGO_OK:
        print("pymongo gerekli: pip install pymongo"); sys.exit(1)

    db = get_backup_db()
    print(f"Backup DB bağlantısı kuruldu: {BACKUP_DB}")

    if args.create_indexes:
        create_indexes(db)

    if args.migrate:
        source_dir = Path(args.source_dir)
        langs = ALL_LANGS if args.all_langs else [args.lang]
        total = 0
        print(f"\nMigrasyon başlıyor ({len(langs)} dil)...")
        for lang in langs:
            total += migrate_lang(lang, db, source_dir)
        print(f"\nToplam {total} kayıt yazıldı → {BACKUP_DB}")

    if args.verify:
        verify(db)


if __name__ == "__main__":
    main()
