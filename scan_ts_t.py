"""
Find t('key', lang) calls with the same key used 3+ times in one file.
These are candidates for const extraction before the return.
"""
import re, glob, os, collections

T_CALL_RE = re.compile(r"\bt\(\s*'([^']+)'\s*,\s*\w+\s*\)")

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

hits = []
for f in glob.glob(base + '/**/*.tsx', recursive=True):
    parts = f.replace(base, '').split(os.sep)
    if set(parts) & SKIP_DIRS:
        continue
    fname = os.path.basename(f)
    try:
        src = open(f, encoding='utf-8').read()
    except:
        continue

    counts = collections.Counter(T_CALL_RE.findall(src))
    for key, cnt in counts.items():
        if cnt >= 3:
            hits.append((cnt, fname, key))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, key in hits[:30]:
    k = fname + ':' + key
    if k not in seen:
        seen.add(k)
        print(str(c) + 'x  ' + fname + '  t(\'' + key + '\')')
