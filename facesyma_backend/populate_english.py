#!/usr/bin/env python
"""
Populate English .po file with translations (for English, msgstr = msgid)
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent


def populate_english_po():
    """Fill English .po file with msgstr = msgid"""
    po_file = BASE_DIR / 'locale' / 'en' / 'LC_MESSAGES' / 'django.po'

    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find msgid/msgstr pairs
    # Match msgid with its msgstr (which may be empty)
    pattern = r'(msgid "[^"]*")\nmsgstr ""'

    def replace_func(match):
        msgid_line = match.group(1)
        # Extract the string content
        return msgid_line + '\nmsgstr ' + msgid_line[6:]

    # Replace all empty msgstr with the msgid
    content = re.sub(pattern, replace_func, content)

    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # Count translations
    count = content.count('msgstr "')
    print(f'✅ English .po file populated with {count - 1} translations (header excluded)')


if __name__ == '__main__':
    populate_english_po()
