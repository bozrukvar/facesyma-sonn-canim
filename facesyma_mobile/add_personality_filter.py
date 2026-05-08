"""
Inserts 'community.filter_personality' after every 'community.filter_all'
line in all 18 language blocks of i18n.ts.
"""

import re
from pathlib import Path

I18N_PATH = Path(__file__).parent / 'src' / 'utils' / 'i18n.ts'

# Map each unique filter_all value → filter_personality translation
PERSONALITY = {
    'Tümü':      'Kişilik',
    'All':       'Personality',
    'Alle':      'Persönlichkeit',
    'Все':       'Личность',
    'الكل':      'الشخصية',
    'Todo':      'Personalidad',
    '전체':       '성격',
    'すべて':     '個性',
    '全部':       '个性',
    'सभी':       'व्यक्तित्व',
    'Tout':      'Personnalité',
    'Tudo':      'Personalidade',
    'সব':        'ব্যক্তিত্ব',
    'Semua':     'Kepribadian',
    'سب':        'شخصیت',
    'Tutto':     'Personalità',
    'Tất cả':   'Tính cách',
    'Wszystkie': 'Osobowość',
}

text = I18N_PATH.read_text(encoding='utf-8')

# Guard: don't insert if already present
if "'community.filter_personality'" in text:
    print("Already present — nothing to do.")
    exit(0)

inserted = 0
for all_val, pers_val in PERSONALITY.items():
    pattern = f"'community.filter_all': '{all_val}',"
    replacement = (
        f"'community.filter_all': '{all_val}',\n"
        f"    'community.filter_personality': '{pers_val}',"
    )
    new_text = text.replace(pattern, replacement, 1)
    if new_text != text:
        text = new_text
        inserted += 1
    else:
        print(f"  WARNING: pattern not found for lang with filter_all='{all_val}'")

I18N_PATH.write_text(text, encoding='utf-8')
print(f"Inserted filter_personality after {inserted} filter_all entries.")
