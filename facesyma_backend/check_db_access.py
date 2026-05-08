#!/usr/bin/env python3
"""
check_db_access.py
==================
MongoDB erişim kalitesi kontrolü.

Şu hataların bir daha yaşanmaması için:
  - Hardcoded DB adı ('facesyma-backend', 'facesyma_db', vb.) mongo.py dışında yasaklı
  - Her yeni dosyanın get_db() import etmesi zorunlu

Kullanım:
  python check_db_access.py          # 0 = OK, 1 = ihlal var
  python check_db_access.py --fix    # otomatik düzeltme önerisi

CI/pre-commit hook olarak ekle:
  # .git/hooks/pre-commit veya CI yaml
  python facesyma_backend/check_db_access.py || exit 1
"""
import re
import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Kurallar ──────────────────────────────────────────────────────────────────

# Bu string'ler mongo.py dışında hiçbir dosyada bulunmamalı
BANNED_PATTERNS = [
    # String literal DB access — variable-based access like [db_name] is fine
    (re.compile(r'''_get_main_client\(\)\[['"]'''), "Hardcoded DB access — use 'from admin_api.utils.mongo import get_db'"),
    (re.compile(r"MongoClient\("),                  "Direct MongoClient() — use admin_api.utils.mongo connection pool"),
    (re.compile(r"'facesyma_db'"),                  "Wrong DB name 'facesyma_db' — correct name is 'facesyma-backend'"),
    (re.compile(r'"facesyma_db"'),                  "Wrong DB name \"facesyma_db\" — correct name is 'facesyma-backend'"),
]

# Bu dosyalar kuraldan muaf (canonical source + standalone scripts)
EXEMPT_FILES = {
    os.path.join('admin_api', 'utils', 'mongo.py'),  # canonical source — DB adı burada tanımlı
    'check_db_access.py',                             # this file
}

# Bu prefix'lerle başlayan dosyalar muaf (standalone migration/seed/test scripts)
EXEMPT_PREFIXES = (
    'seed_', 'migrate_', 'setup_', 'test_', 'add_image', 'patch_',
    'generate_', 'setup_admin',
)

# Bu dizinler tamamen muaf (standalone script collections)
EXEMPT_DIRS = {
    'algorithm_patch',  # one-off patch scripts
}

# Bu dizinler taranmaz
SKIP_DIRS = {'__pycache__', '.git', 'migrations', 'venv', '.venv', 'node_modules'}

# Sadece uygulama kodu bu kurallarla kontrol edilir
# facesyma_revize'nin kendi database.py'leri mimari gereği standalone → muaf
EXEMPT_REVIZE_STANDALONE = {
    os.path.join('facesyma_revize', 'database.py'),
    os.path.join('facesyma_revize', 'database_30.py'),
    os.path.join('facesyma_revize', 'database_advisor.py'),
    os.path.join('facesyma_revize', 'database_daily.py'),
    os.path.join('facesyma_revize', 'database_motivate.py'),
    os.path.join('facesyma_revize', 'database_twins.py'),
    os.path.join('facesyma_revize', 'database_twins_30.py'),
    os.path.join('facesyma_revize', 'contrast.py'),
    os.path.join('facesyma_revize', 'similarity_matcher.py'),
    os.path.join('gamification', 'migrate_game_indexes.py'),
    os.path.join('gamification', 'seed_challenges.py'),
}


def _is_exempt(rel: str, fname: str) -> bool:
    if rel in EXEMPT_FILES or rel in EXEMPT_REVIZE_STANDALONE:
        return True
    # Standalone scripts by filename prefix
    if any(fname.startswith(p) for p in EXEMPT_PREFIXES):
        return True
    # Exempt directories
    parts = rel.split(os.sep)
    if any(part in EXEMPT_DIRS for part in parts):
        return True
    return False


def scan() -> list[dict]:
    violations = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fp = os.path.join(root, fname)
            rel = os.path.relpath(fp, BASE_DIR)
            if _is_exempt(rel, fname):
                continue
            try:
                with open(fp, encoding='utf-8', errors='ignore') as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                for pattern, message in BANNED_PATTERNS:
                    if pattern.search(line):
                        violations.append({
                            'file': rel,
                            'line': i,
                            'content': line.rstrip(),
                            'message': message,
                        })
    return violations


def main():
    parser = argparse.ArgumentParser(description='MongoDB access pattern linter')
    parser.add_argument('--fix', action='store_true', help='Show fix suggestions')
    args = parser.parse_args()

    violations = scan()

    if not violations:
        print('✅  DB access check passed — no violations found.')
        return 0

    print(f'❌  Found {len(violations)} DB access violation(s):\n')
    for v in violations:
        print(f"  {v['file']}:{v['line']}")
        print(f"    Code:    {v['content'].strip()}")
        print(f"    Problem: {v['message']}")
        if args.fix:
            print(f"    Fix:     Replace with 'from admin_api.utils.mongo import get_db'")
        print()

    print('─' * 60)
    print('Fix: Replace hardcoded DB access with the canonical import:')
    print()
    print('  from admin_api.utils.mongo import get_db')
    print()
    print('  # Usage:')
    print("  db = get_db()                    # main DB")
    print("  col = get_db()['my_collection']  # specific collection")
    print()
    print('DB name is defined ONCE in admin_api/utils/mongo.py.')
    print('Never write the DB name string in any other file.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
