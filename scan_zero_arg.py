import ast, glob, os

def scan(path):
    try:
        src = open(path, encoding='utf-8').read()
        tree = ast.parse(src)
    except:
        return []
    results = []
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = {}
        for node in ast.walk(func):
            if isinstance(node, ast.Call):
                if len(getattr(node, 'args', [])) == 0 and len(getattr(node, 'keywords', [])) == 0:
                    try:
                        key = ast.unparse(node)
                        calls[key] = calls.get(key, 0) + 1
                    except:
                        pass
        for k, v in calls.items():
            skip = ['_get_db', 'datetime', 'utcnow', 'now()', 'time()', 'uuid', 'super()',
                    'list()', 'dict()', 'set()', 'tuple()', 'str()', 'int()', 'bool()']
            if v >= 2 and not any(s in k for s in skip):
                results.append((v, os.path.basename(path), func.name, k))
    return results

SKIP_DIRS = {'finetune', '__pycache__', 'node_modules', '.git', 'migrations'}
SKIP_FILES = ['test_', 'tests_', 'audit_', 'train', 'scan_hot', 'migrate', 'compile_',
              'smart_', 'translate_', 'scan_zero']
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim'

hits = []
for f in glob.glob(base + '/**/*.py', recursive=True):
    fname = os.path.basename(f)
    if any(s in fname for s in SKIP_FILES):
        continue
    parts = f.replace(base, '').replace('/', os.sep).split(os.sep)
    if set(parts) & SKIP_DIRS:
        continue
    hits.extend(scan(f))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, fn, p in hits[:40]:
    key = fname + ':' + fn + ':' + p
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + ':' + fn + '  ' + p)
