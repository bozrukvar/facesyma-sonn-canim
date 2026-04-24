"""Find repeated dict.get('same_key') calls in same function (excluding comprehensions)."""
import ast, glob, os, collections

def scan(path):
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
        counts = collections.Counter()
        for node in walk_no_comp(func):
            # Match: obj.get('key') or obj.get("key") - 1 string arg
            if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'get' and
                    len(node.args) >= 1 and
                    isinstance(node.args[0], ast.Constant) and
                    isinstance(node.args[0].value, str)):
                try:
                    obj = ast.unparse(node.func.value)
                    key = node.args[0].value
                    counts[(obj, key)] += 1
                except:
                    pass
        for (obj, key), cnt in counts.items():
            if cnt >= 2:
                results.append((cnt, os.path.basename(path), func.name,
                                f"{obj}.get('{key}')"))
    return results

SKIP_DIRS = {'finetune', '__pycache__', 'node_modules', '.git', 'migrations'}
SKIP_FILES = ['test_', 'tests_', 'audit_', 'train', 'scan_', 'migrate', 'compile_',
              'smart_', 'translate_']
base = r'c:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim'

hits = []
for f in glob.glob(base + '/**/*.py', recursive=True):
    fname = os.path.basename(f)
    if any(s in fname for s in SKIP_FILES):
        continue
    parts = f.replace(base, '').split(os.sep)
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
