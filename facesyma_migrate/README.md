# Facesyma Migration Scripts

## Kurulum
pip install -r requirements.txt

## Çalıştırma Sırası

1. python verify_migration.py
2. python migrate_sentences.py --dry-run --langs en
3. python migrate_sentences.py --langs en
4. python migrate_sentences.py
5. python migrate_json.py --dry-run --langs en
6. python migrate_json.py --langs en
7. python migrate_json.py
8. python verify_migration.py

## Dosyalar
- migrate_sentences.py → MongoDB attribute + advisor + daily
- migrate_json.py      → sifat_veritabani.json × 7 dil
- verify_migration.py  → audit tablosu

## Diller: en, de, ru, ar, es, ko, ja
