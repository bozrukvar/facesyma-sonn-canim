#!/usr/bin/env python
"""
Manual .po to .mo compilation script (no gettext required)
Compiles .po files to binary .mo format for Django i18n
"""

import struct
import array
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def generate_hash(string):
    """Generate hash for quick lookup in .mo file"""
    hash_value = 0
    for char in string:
        hash_value = hash_value * 33 + ord(char)
    return (hash_value & 0x7FFFFFFF)


def write_mo_file(po_file_path, mo_file_path):
    """
    Compile .po file to .mo (binary) format
    Based on GNU gettext .mo format spec
    """
    messages = []
    ids = []
    strs = []

    # Parse .po file
    with open(po_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header and comments
        if not line or line.startswith('#'):
            i += 1
            continue

        # Parse msgid
        if line.startswith('msgid'):
            # Extract string
            msgid_val = line[6:].strip()
            if msgid_val.startswith('"') and msgid_val.endswith('"'):
                msgid_val = msgid_val[1:-1]
            else:
                msgid_val = ''

            # Check for multiline strings
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('"') and next_line.endswith('"'):
                    msgid_val += next_line[1:-1]
                    i += 1
                else:
                    break

            # Parse msgstr
            msgstr_val = ''
            if lines[i].strip().startswith('msgstr'):
                msgstr_line = lines[i].strip()[7:].strip()
                if msgstr_line.startswith('"') and msgstr_line.endswith('"'):
                    msgstr_val = msgstr_line[1:-1]

                # Check for multiline strings
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith('"') and next_line.endswith('"'):
                        msgstr_val += next_line[1:-1]
                        i += 1
                    else:
                        break
            else:
                i += 1

            # Skip empty header
            if msgid_val or msgstr_val:
                ids.append(msgid_val)
                strs.append(msgstr_val)
                messages.append((msgid_val, msgstr_val))
        else:
            i += 1

    # Write .mo file in GNU gettext format
    # Format: magic number, version, number of strings, offset of table,
    # offset of hash table, hash table size

    # Encode strings to UTF-8
    ids_data = [m[0].encode('utf-8') for m in messages]
    strs_data = [m[1].encode('utf-8') for m in messages]

    # Create offset tables
    keyoffset = 7 * 4 + 16 * len(messages)
    valueoffset = keyoffset + sum(len(k) + 1 for k in ids_data)

    koffsets = []
    voffsets = []
    offset = keyoffset
    for k in ids_data:
        koffsets.append(offset)
        offset += len(k) + 1

    offset = valueoffset
    for v in strs_data:
        voffsets.append(offset)
        offset += len(v) + 1

    # Write file
    with open(mo_file_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('Iiiiiii',
                           0xde120495,           # magic
                           0,                    # version
                           len(messages),        # number of entries
                           7*4,                  # offset of table with original strings
                           7*4 + 8*len(messages),  # offset of table with translated strings
                           0,                    # size of hash table
                           0))                   # offset of hash table

        # Original string table
        for k in ids_data:
            f.write(struct.pack('ii', len(k), koffsets[ids_data.index(k)]))

        # Translated string table
        for v in strs_data:
            f.write(struct.pack('ii', len(v), voffsets[strs_data.index(v)]))

        # Strings
        for k in ids_data:
            f.write(k)
            f.write(b'\x00')

        for v in strs_data:
            f.write(v)
            f.write(b'\x00')

    return len(messages)


def main():
    """Compile all .po files to .mo"""
    print('\n🔨 Compiling .po files to .mo format...\n')

    locale_dir = BASE_DIR / 'locale'
    compiled_count = 0
    total_strings = 0

    for lang_dir in sorted(locale_dir.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name.startswith('.'):
            continue

        po_file = lang_dir / 'LC_MESSAGES' / 'django.po'
        mo_file = lang_dir / 'LC_MESSAGES' / 'django.mo'

        if po_file.exists():
            try:
                count = write_mo_file(po_file, mo_file)
                compiled_count += 1
                total_strings += count
                print(f'✓ {lang_dir.name:12} — {mo_file.name:15} ({count:3} strings)')
            except Exception as e:
                print(f'✗ {lang_dir.name:12} — ERROR: {e}')

    print(f'\n✅ Compilation complete!')
    print(f'   {compiled_count} .mo files created ({total_strings} total strings)')
    print(f'\nNext steps:')
    print(f'1. Start Django server: python manage.py runserver')
    print(f'2. Test languages:')
    print(f'   curl -H "Accept-Language: tr" http://localhost:8000/api/v1/admin/gamification-dashboard/')
    print(f'   curl -H "Accept-Language: es" http://localhost:8000/api/v1/admin/gamification-dashboard/')


if __name__ == '__main__':
    main()
