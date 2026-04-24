"""
Extended scan: find map/filter/forEach callbacks where the param's
property is accessed 2+ times (lower threshold than previous scan).
Also catches flatMap and renderItem patterns.
"""
import re, glob, os, collections

CALLBACK_RE = re.compile(
    r'(?:\.map|\.filter|\.forEach|\.flatMap|renderItem)\s*[=(]\s*\(?\s*'
    r'\{?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?:,\s*\w+)?\s*\}?\s*\)?\s*(?:=>|{)'
)

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

ALWAYS_SKIP = {'item', 'i', 'idx', 'index', '_', 'e', 'v', 'res', 'key',
               'val', 'el', 'n', 'x', 'p', 'a', 'b', 'c', 'd', 'f', 'g'}

hits = []
for f in glob.glob(base + '/**/*.ts', recursive=True) + glob.glob(base + '/**/*.tsx', recursive=True):
    parts = f.replace(base, '').split(os.sep)
    if set(parts) & SKIP_DIRS:
        continue
    fname = os.path.basename(f)
    try:
        src = open(f, encoding='utf-8').read()
    except:
        continue

    for m in CALLBACK_RE.finditer(src):
        param = m.group(1)
        if param in ALWAYS_SKIP or param.startswith('{'):
            continue

        start = m.start()
        window = src[start:start+800]

        prop_re = re.compile(r'\b' + re.escape(param) + r'\.([a-zA-Z_$][a-zA-Z0-9_$]*)\b(?!\s*[\(\[])')
        prop_counts = collections.Counter()
        for pm in prop_re.finditer(window):
            prop_counts[pm.group(1)] += 1

        for prop, cnt in prop_counts.items():
            if cnt >= 2:
                hits.append((cnt, fname, param, prop))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, param, prop in hits[:40]:
    key = fname + ':' + param + '.' + prop
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + param + '.' + prop)
