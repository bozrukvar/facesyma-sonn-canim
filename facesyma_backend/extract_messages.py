#!/usr/bin/env python
"""
Manual message extraction script for i18n on Windows (no xgettext required)
Extracts translatable strings from translation_service.py and templates
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

def extract_from_translation_service():
    """Extract strings from admin_api/services/translation_service.py"""
    strings = []
    file_path = BASE_DIR / 'admin_api' / 'services' / 'translation_service.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all _('...') patterns
    pattern = r"_\('([^']+)'\)"
    matches = re.findall(pattern, content)

    for match in matches:
        strings.append({
            'text': match,
            'location': f'admin_api/services/translation_service.py',
            'context': ''
        })

    return strings


def extract_from_templates():
    """Extract strings from templates with {% trans %} tags"""
    strings = []
    template_dir = BASE_DIR / 'admin_api' / 'templates'

    if template_dir.exists():
        for template_file in template_dir.glob('*.html'):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find {% trans "..." %} patterns
            pattern = r'{%\s*trans\s+"([^"]+)"\s*%}'
            matches = re.finditer(pattern, content)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                strings.append({
                    'text': match.group(1),
                    'location': f'admin_api/templates/{template_file.name}:{line_num}',
                    'context': ''
                })

    return strings


def create_po_file(language_code, language_name, strings):
    """Create a .po file for the given language"""
    locale_dir = BASE_DIR / 'locale' / language_code / 'LC_MESSAGES'
    locale_dir.mkdir(parents=True, exist_ok=True)

    po_file = locale_dir / 'django.po'

    # Group strings by text (deduplicate)
    unique_strings = {}
    for s in strings:
        _st = s['text']
        if _st not in unique_strings:
            unique_strings[_st] = []
        _ust = unique_strings[_st]
        _ust.append(s['location'])

    # Create .po file content
    header = f'''# {language_name} translations for Gamification Phase 2
# Copyright (C) 2026
# This file is distributed under the same license as the package.
#
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: {language_code}\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''

    entries = []
    # Add string entries
    for text, locations in sorted(unique_strings.items()):
        locations_str = ", ".join(locations[:3])
        entry = f'''#: {locations_str}
msgid "{text}"
msgstr ""

'''
        entries.append(entry)

    po_content = header + ''.join(entries)

    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(po_content)

    print(f'✓ Created {po_file}')
    return po_file


def create_pot_file(strings):
    """Create a .pot template file"""
    locale_dir = BASE_DIR / 'locale'
    locale_dir.mkdir(parents=True, exist_ok=True)

    pot_file = locale_dir / 'django.pot'

    # Group strings by text (deduplicate)
    unique_strings = {}
    for s in strings:
        _st = s['text']
        if _st not in unique_strings:
            unique_strings[_st] = []
        _ust = unique_strings[_st]
        _ust.append(s['location'])

    # Create .pot file content
    creation_date = datetime.now().isoformat()
    header = f'''# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: Gamification Phase 2\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: {creation_date}\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

'''

    entries = []
    # Add string entries
    for text, locations in sorted(unique_strings.items()):
        locations_str = ", ".join(locations[:3])
        entry = f'''#: {locations_str}
msgid "{text}"
msgstr ""

'''
        entries.append(entry)

    pot_content = header + ''.join(entries)

    with open(pot_file, 'w', encoding='utf-8') as f:
        f.write(pot_content)

    print(f'✓ Created {pot_file} ({len(unique_strings)} strings)')
    return pot_file


def main():
    """Main extraction function"""
    print('\n📦 Extracting translatable strings...\n')

    # Extract all strings
    service_strings = extract_from_translation_service()
    template_strings = extract_from_templates()
    all_strings = service_strings + template_strings

    print(f'Found {len(all_strings)} translatable strings')
    print(f'  - From translation_service.py: {len(service_strings)}')
    print(f'  - From templates: {len(template_strings)}')

    # Create .pot template
    print('\n📄 Creating template file...')
    create_pot_file(all_strings)

    # Create .po files for all languages
    print('\n🌍 Creating .po files for all languages...\n')

    languages = [
        ('en', 'English'),
        ('tr', 'Türkçe'),
        ('de', 'Deutsch'),
        ('fr', 'Français'),
        ('es', 'Español'),
        ('it', 'Italiano'),
        ('pt', 'Português'),
        ('pl', 'Polski'),
        ('ru', 'Русский'),
        ('ja', '日本語'),
        ('zh-hans', '简体中文'),
        ('zh-hant', '繁體中文'),
        ('ko', '한국어'),
        ('ar', 'العربية'),
        ('he', 'עברית'),
        ('hi', 'हिन्दी'),
        ('vi', 'Tiếng Việt'),
        ('th', 'ไทย'),
    ]

    for code, name in languages:
        create_po_file(code, name, all_strings)

    print(f'\n✅ Message extraction complete!')
    print(f'\nNext steps:')
    print(f'1. Edit .po files in locale/{{lang}}/LC_MESSAGES/django.po')
    print(f'2. Run: python manage.py compilemessages')
    print(f'3. Test with: curl -H "Accept-Language: tr" http://localhost:8000/...')


if __name__ == '__main__':
    main()
