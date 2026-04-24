"""
Scan TypeScript/TSX for repeated property chains (obj.prop.sub, obj.prop)
Reports patterns used 3+ times in same function/arrow-function body.
Uses simple regex (no full TS AST).
"""
import re, glob, os, collections

# Match property chains: word.word, word.word.word (no parens after)
CHAIN_RE = re.compile(r'\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\.[a-zA-Z_$][a-zA-Z0-9_$]+){1,3})\b(?!\s*[\(\[])')

SKIP_PREFIXES = ('console.', 'Math.', 'Object.', 'Array.', 'JSON.', 'Date.', 'Promise.',
                 'React.', 'StyleSheet.', 'Platform.', 'Animated.', 'NativeModules.',
                 'window.', 'process.', 'module.', 'exports.', 'require.', 'Symbol.')

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

    # Split into rough "function bodies" by scanning for { } blocks — approximate
    # Instead: just scan per-file and report chains with 4+ occurrences in the whole file
    counts = collections.Counter()
    for m in CHAIN_RE.finditer(src):
        chain = m.group(1)
        if any(chain.startswith(p) for p in SKIP_PREFIXES):
            continue
        if chain.count('.') < 1:
            continue
        counts[chain] += 1

    for chain, cnt in counts.most_common(10):
        if cnt >= 4:
            hits.append((cnt, fname, chain))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, chain in hits[:50]:
    key = fname + ':' + chain
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + '  ' + chain)
