"""
Scan for repeated state/prop/route.params accesses in TSX render bodies.
Specifically: route.params.X used 2+ times, state?.field used 2+ times.
"""
import re, glob, os, collections

SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'build', 'dist', '.expo'}
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim\facesyma_mobile\src'

# Match optional chains: word?.word, word?.word?.word, etc.
OPT_CHAIN_RE = re.compile(
    r'\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\??\.[a-zA-Z_$][a-zA-Z0-9_$]+){1,4})\b(?!\s*[\(\[])'
)

SKIP_STARTS = ('styles.', 'colors.', 'spacing.', 'typography.', 'React.',
               'Platform.', 'StyleSheet.', 'Animated.', 'console.', 'Math.',
               'Object.', 'Array.', 'JSON.', 'Promise.')

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

    counts = collections.Counter()
    for m in OPT_CHAIN_RE.finditer(src):
        chain = m.group(1)
        if any(chain.startswith(s) for s in SKIP_STARTS):
            continue
        if '?' in chain:  # Only optional chains
            counts[chain] += 1

    for chain, cnt in counts.items():
        if cnt >= 3:
            hits.append((cnt, fname, chain))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, chain in hits[:40]:
    key = fname + ':' + chain
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + chain)
