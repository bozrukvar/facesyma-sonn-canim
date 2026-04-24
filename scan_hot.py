import ast, collections, os, glob

def scan_funcs(path):
    try:
        src = open(path, encoding='utf-8').read()
        tree = ast.parse(src)
    except:
        return []
    def walk_no_comp(node):
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                continue
            yield from walk_no_comp(child)
    results = []
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        patterns = collections.Counter()
        for node in walk_no_comp(func):
            if isinstance(node, ast.Attribute):
                key = ast.unparse(node.value) + '.' + node.attr
                if not key.startswith('self.'):
                    patterns[key] += 1
            elif isinstance(node, ast.Subscript):
                try:
                    key = ast.unparse(node.value) + '[' + ast.unparse(node.slice) + ']'
                    patterns[key] += 1
                except:
                    pass
        for p, c in patterns.most_common(3):
            if c >= 2:
                results.append((c, func.name, p))
    return results

base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim'
SKIP_DIRS = {'finetune', '__pycache__', 'node_modules', '.git', 'migrations'}
SKIP_FILES = ['test_', 'tests_', 'audit_', 'train', 'scan_hot', 'migrate', 'compile_', 'smart_', 'translate_']
hits = []
for f in glob.glob(base + '/**/*.py', recursive=True):
    fname = os.path.basename(f)
    if any(s in fname for s in SKIP_FILES):
        continue
    fparts = set(f.replace(base, '').replace('\\', '/').split('/'))
    if fparts & SKIP_DIRS:
        continue
    for c, fn, p in scan_funcs(f):
        hits.append((c, fname, fn, p))

hits.sort(key=lambda x: -x[0])
seen = set()
for c, fname, fn, p in hits:
    key = fname + ':' + fn + ':' + p
    if key not in seen:
        seen.add(key)
        print(str(c) + 'x  ' + fname + ':' + fn + '  ' + p)
