"""
Scan TSX render bodies for repeated .length accesses on same variable.
Also: repeated obj?.prop?.sub chains (optional chaining).
"""
import re, glob, os, collections

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

# Match: word.length or word?.length or word?.prop or word.prop.subprop
LENGTH_RE = re.compile(r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)(?:\??)\.length\b')
OPT_CHAIN_RE = re.compile(r'\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\??\.[a-zA-Z_$][a-zA-Z0-9_$]+){2,4})\b')

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

    # Count .length accesses per variable
    lcounts = collections.Counter()
    for m in LENGTH_RE.finditer(src):
        var = m.group(1)
        if var not in ('styles', 'colors', 'spacing', 'typography', 'theme'):
            lcounts[var + '.length'] += 1

    for expr, cnt in lcounts.items():
        if cnt >= 3:
            hits.append((cnt, fname, expr))

    # Count optional chain accesses
    ocounts = collections.Counter()
    for m in OPT_CHAIN_RE.finditer(src):
        chain = m.group(1)
        skip = ['styles.', 'colors.', 'spacing.', 'typography.', 'React.',
                'Platform.', 'StyleSheet.', 'Animated.', 'console.']
        if not any(chain.startswith(s) for s in skip):
            ocounts[chain] += 1

    for chain, cnt in ocounts.items():
        if cnt >= 4:
            hits.append((cnt, fname, chain))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, p in hits[:50]:
    key = fname + ':' + p
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + p)
