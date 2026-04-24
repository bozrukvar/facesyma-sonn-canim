"""
Scan TypeScript store/slice files and utility files for repeated
property chains (state.field, action.payload.x) used 3+ times.
"""
import re, glob, os, collections

CHAIN_RE = re.compile(
    r'\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\??\.[a-zA-Z_$][a-zA-Z0-9_$]+){1,4})\b(?!\s*[\(\[])'
)

SKIP_STARTS = ('console.', 'Math.', 'Object.', 'Array.', 'JSON.', 'Date.',
               'Promise.', 'React.', 'StyleSheet.', 'Platform.', 'Animated.',
               'window.', 'process.', 'module.', 'exports.', 'require.',
               'styles.', 'colors.', 'spacing.', 'typography.')

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

    counts = collections.Counter()
    for m in CHAIN_RE.finditer(src):
        chain = m.group(1)
        if any(chain.startswith(s) for s in SKIP_STARTS):
            continue
        # Focus on state/action/payload/route chains + 2+ dots
        if chain.count('.') >= 1:
            counts[chain] += 1

    for chain, cnt in counts.items():
        if cnt >= 4 and '?' not in chain:
            hits.append((cnt, fname, chain))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, chain in hits[:50]:
    key = fname + ':' + chain
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + chain)
