"""
apply_offline_error.py
======================
Applies useOfflineError hook to all screens:

1. Adds import { useOfflineError } from '../hooks/useOfflineError'
2. Adds `const getErrorMessage = useOfflineError();` after `useLanguage()`
3. Replaces `VAR?.response?.data?.detail || t(...)` with `getErrorMessage(VAR)`
   for VAR in {e, err, error} — catches both optional-chain and direct access
4. Skips screens that have no API catch pattern or already use the hook
"""

import re
import os
import glob

SRC = os.path.join(os.path.dirname(__file__), '..', 'facesyma_mobile', 'src', 'screens')
files = sorted(glob.glob(os.path.join(SRC, '*.tsx')))

# Pattern: e?.response?.data?.detail || t('...', lang)
# or:      e.response?.data?.detail  || t('...', lang)
# Capture group 1 = variable name, rest = noise we replace
DETAIL_RE = re.compile(
    r'(e|err|error)\??\.response\??\.data\??\.(?:detail|message)\s*\|\|\s*t\([^)]+\)',
    re.MULTILINE,
)

# Also catch the simpler fallback: t('common.generic_error', lang) ALONE inside a catch
# (only when it's the direct error message, not a validation-stage setError)
# We DON'T replace these automatically — too risky to misidentify validation errors.

stats = {'files': 0, 'replacements': 0}

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        content = f.read()

    original = content

    # Skip if no API error detail pattern
    if not DETAIL_RE.search(content):
        continue

    # Skip if already using the hook
    if 'useOfflineError' in content:
        continue

    # ── 1. Add import ─────────────────────────────────────────────────────────
    # Insert after the last local import block (before the first blank line
    # following imports, or after the last 'import ...' line).
    import_line = "import { useOfflineError } from '../hooks/useOfflineError';\n"
    # Find position: insert right after the last import line
    last_import = max(
        (m.end() for m in re.finditer(r'^import .+;\n', content, re.MULTILINE)),
        default=0,
    )
    content = content[:last_import] + import_line + content[last_import:]

    # ── 2. Add hook call ──────────────────────────────────────────────────────
    # Find `const { lang } = useLanguage();` or `const lang = ...useLanguage`
    lang_hook = re.search(
        r'(const \{[^}]*\blang\b[^}]*\} = useLanguage\(\);|'
        r'const lang = .*useLanguage.*;\n)',
        content,
    )
    if lang_hook:
        insert_pos = lang_hook.end()
        hook_line = '  const getErrorMessage = useOfflineError();\n'
        content = content[:insert_pos] + hook_line + content[insert_pos:]
    else:
        # Fallback: find first useState/useSelector line
        first_hook = re.search(r'(  const \[.+\] = useState)', content)
        if first_hook:
            insert_pos = first_hook.start()
            content = content[:insert_pos] + '  const getErrorMessage = useOfflineError();\n' + content[insert_pos:]

    # ── 3. Replace detail-or-fallback pattern ─────────────────────────────────
    def replacer(m: re.Match) -> str:
        var = m.group(1)
        return f'getErrorMessage({var})'

    new_content, n = DETAIL_RE.subn(replacer, content)
    content = new_content
    stats['replacements'] += n

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        stats['files'] += 1
        print(f'  {os.path.basename(fpath)}: {n} replacement(s)')

print(f"\nTotal: {stats['files']} files, {stats['replacements']} replacements")
