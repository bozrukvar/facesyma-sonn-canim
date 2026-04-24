"""
Find map callbacks where a single-letter or short parameter's property
is accessed 3+ times — prime candidates for parameter destructuring.
"""
import re, glob, os, collections

# Match patterns like: variable.property used repeatedly
# Look for .map(x => ...) or .map((x, i) => ...) patterns
MAP_PARAM_RE = re.compile(r'\.map\(\s*\(?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?:,\s*\w+)?\s*\)?\s*=>')

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

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

    # Find each map call and extract the parameter name
    for m in MAP_PARAM_RE.finditer(src):
        param = m.group(1)
        if param in ('item', 'i', 'idx', 'index', '_', 'e', 'v', 'res', 'key', 'val'):
            continue

        # Get a window of code after the match (the callback body)
        start = m.start()
        window = src[start:start+600]

        # Count param.prop accesses in this window
        prop_re = re.compile(r'\b' + re.escape(param) + r'\.([a-zA-Z_$][a-zA-Z0-9_$]*)\b(?!\s*\()')
        prop_counts = collections.Counter()
        for pm in prop_re.finditer(window):
            prop_counts[pm.group(1)] += 1

        for prop, cnt in prop_counts.items():
            if cnt >= 3:
                hits.append((cnt, fname, param, prop))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, param, prop in hits[:30]:
    key = fname + ':' + param + '.' + prop
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + param + '.' + prop)
