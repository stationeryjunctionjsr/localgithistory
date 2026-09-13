import ast
import glob
import os

routers_dir = 'backend/app/routers'
router_files = sorted(glob.glob(os.path.join(routers_dir, '*.py')))

issues = []

for fpath in router_files:
    fname = os.path.basename(fpath)
    if fname == '__init__.py':
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=fpath)
    
    # Check each function scope
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_dicts = set()
            for stmt in ast.walk(fn):
                if isinstance(stmt, ast.Assign):
                    if isinstance(stmt.value, ast.Dict):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                local_dicts.add(target.id)
                elif isinstance(stmt, ast.AnnAssign):
                    if isinstance(stmt.value, ast.Dict) and isinstance(stmt.target, ast.Name):
                        local_dicts.add(stmt.target.id)
            
            # Now find attribute access on local_dicts
            for node in ast.walk(fn):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id in local_dicts:
                        # Exclude standard dict methods like .keys, .values, .items, .copy, .clear, .update, .pop, .get
                        if node.attr not in ('keys', 'values', 'items', 'copy', 'clear', 'update', 'pop', 'get', 'setdefault', 'popitem'):
                            line_no = node.lineno
                            line_src = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ''
                            issues.append((fname, fn.name, line_no, node.value.id, node.attr, line_src))

print(f"Total attribute accesses on locally declared dicts: {len(issues)}")
for item in issues:
    print(item)
