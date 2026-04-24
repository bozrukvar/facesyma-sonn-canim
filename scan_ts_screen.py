"""
Scan TSX screens for:
1. route.params.X used 2+ times in same file
2. state.X.Y used 3+ times in same file (Redux state)
3. Repeated string literals 'same.key' used 3+ times (t() call keys)
"""
import re, glob, os, collections

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

# route.params.X pattern
PARAMS_RE = re.compile(r'\broute\.params\.([a-zA-Z_$][a-zA-Z0-9_$]*)\b')
# state.X.Y chains (redux)
STATE_CHAIN_RE = re.compile(r'\bstate\.([a-zA-Z_$][a-zA-Z0-9_$]*\.[a-zA-Z_$][a-zA-Z0-9_$]*)\b')
# useSelector(state => state.X.Y) — extract the chain
SELECTOR_RE = re.compile(r'useSelector\s*\([^)]*\bstate\.([a-zA-Z_$][a-zA-Z0-9_$]*)\b')

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

    # route.params.X
    pc = collections.Counter(PARAMS_RE.findall(src))
    for param, cnt in pc.items():
        if cnt >= 2:
            hits.append((cnt, fname, f'route.params.{param}'))

    # Repeated useSelector slice names (indicates multiple selectors for same slice)
    sc = collections.Counter(SELECTOR_RE.findall(src))
    for slice_name, cnt in sc.items():
        if cnt >= 3:
            hits.append((cnt, fname, f'useSelector(state.{slice_name}) x{cnt}'))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, p in hits[:40]:
    key = fname + ':' + p
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + p)
