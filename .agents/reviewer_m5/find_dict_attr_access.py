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
    
    # Track assignments to dict literals: x = { ... }
    # and None: x = None
    dict_vars = set()
    none_vars = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Dict):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        dict_vars.add(target.id)
            elif isinstance(node.value, ast.Constant) and node.value.value is None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        none_vars.add(target.id)
        
        # Check attribute access on known dict/none vars
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                var_name = node.value.id
                if var_name in ('coupon_info',):
                    line_no = node.lineno
                    line_src = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ''
                    issues.append((fname, line_no, var_name, node.attr, line_src))

print(f"Total suspicious attribute accesses found on dictionary/None variables: {len(issues)}")
for fname, line_no, var_name, attr, line_src in issues:
    print(f"  {fname}:L{line_no}: {var_name}.{attr} -> {line_src}")
