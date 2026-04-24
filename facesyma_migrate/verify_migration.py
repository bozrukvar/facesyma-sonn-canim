"""
verify_migration.py — Tam veritabanı doğrulama
"""
import os, sys, argparse, logging
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

MONGO_URI = os.environ.get(
    "MONGO_URI",
    ''
)
LANG_MAP = {
    "tr": {"attr": "database_attribute_tr", "daily": "database_daily_tr",  "name": "Türkçe     "},
    "en": {"attr": "database_attribute_en", "daily": "database_daily_en",  "name": "İngilizce  "},
    "de": {"attr": "database_attribute_de", "daily": "database_daily_de",  "name": "Almanca    "},
    "ru": {"attr": "database_attribute_ru", "daily": "database_daily_ru",  "name": "Rusça      "},
    "ar": {"attr": "database_attribute_ar", "daily": "database_daily_ar",  "name": "Arapça     "},
    "es": {"attr": "database_attribute_sp", "daily": None,                  "name": "İspanyolca "},
    "ko": {"attr": "database_attribute_kr", "daily": None,                  "name": "Korece     "},
    "ja": {"attr": "database_attribute_jp", "daily": None,                  "name": "Japonca    "},
}
ATTR_COLS = ["eye", "eyebrow", "lip", "nose", "forehead"]


def audit_attr(client, db_name):
    db    = client[db_name]
    total = 0
    for col in ATTR_COLS:
        for doc in db[col].find({}):
            for vk, vd in doc.items():
                if vk == "_id" or not isinstance(vd, dict):
                    continue
                for sifat, cumleler in vd.items():
                    if sifat not in ("att1","att2") and isinstance(cumleler, list):
                        total += len(cumleler)
    return total


def audit_advisor(client):
    col   = client["facesyma-backend"]["appfaceapi_advisor"]
    _ccd  = col.count_documents
    total = _ccd({})
    langs = {}
    for lang in ["tr","en","de","ru","ar","es","ko","ja"]:
        langs[lang] = _ccd({f"cumle_{lang}": {"$exists": True}})
    return total, langs


def audit_daily(client, db_name):
    if not db_name:
        return 0
    try:
        db    = client[db_name]
        total = 0
        for col in ["positive","negative"]:
            for doc in db[col].find({}):
                for key in ["positive_daily","negative_daily"]:
                    v = doc.get(key, [])
                    if isinstance(v, list):
                        total += len(v)
        return total
    except Exception:
        return 0


def verify(langs):
    _info = log.info
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")
        _info("MongoDB OK ✓\n")
    except Exception as e:
        log.error(f"Bağlantı hatası: {e}"); sys.exit(1)

    # ── 1. Attribute ──────────────────────────────────────────────
    tr_attr = audit_attr(client, "database_attribute_tr")
    _info(f"{'─'*65}")
    _info(f"{'DİL':<14} {'ATTRIBUTE':>10} {'%TR':>6}  {'ADV':>6}  {'DAILY':>7}  DURUM")
    _info(f"{'─'*65}")

    adv_total, adv_langs = audit_advisor(client)

    all_langs = ["tr"] + [l for l in langs if l != "tr"]
    for lang in all_langs:
        info      = LANG_MAP.get(lang, {})
        _iget     = info.get
        attr_n    = audit_attr(client, _iget("attr",""))
        attr_pct  = attr_n / tr_attr * 100 if tr_attr else 0
        adv_n     = adv_langs.get(lang, 0)
        daily_n   = audit_daily(client, _iget("daily"))

        if lang == "tr":
            status = "REFERANS"
        elif attr_pct >= 95 and adv_n >= adv_total * 0.9:
            status = "TAMAM ✓"
        elif attr_pct >= 50:
            status = "EKSIK !"
        else:
            status = "BOŞ   x"

        _info(
            f"{_iget('name',lang):<14} {attr_n:>10,} {attr_pct:>5.1f}%"
            f"  {adv_n:>6,}  {daily_n:>7,}  {status}"
        )

    _info(f"{'─'*65}")
    _info(f"{'':14} {'(hedef)':>10} {'100%':>6}  {adv_total:>6,}  {'?':>7}")
    _info(f"\nappfaceapi_advisor toplam döküman: {adv_total:,}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--langs", default=",".join(k for k in LANG_MAP if k!="tr"))
    args  = p.parse_args()
    langs = [s for l in args.langs.split(",") if (s := l.strip())]
    verify(langs)

if __name__ == "__main__":
    main()
