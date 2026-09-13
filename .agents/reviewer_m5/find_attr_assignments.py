import ast
import glob
import os

routers_dir = 'backend/app/routers'
router_files = sorted(glob.glob(os.path.join(routers_dir, '*.py')))

attribute_assignments_on_dicts = []

for fpath in router_files:
    fname = os.path.basename(fpath)
    if fname == '__init__.py':
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=fpath)
    
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # find all dict variables in this function
            dict_vars = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Dict):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                dict_vars.add(t.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.value, ast.Dict) and isinstance(node.target, ast.Name):
                        dict_vars.add(node.target.id)
            
            # find all attribute assignments to dict_vars
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                            if target.value.id in dict_vars:
                                line_no = node.lineno
                                line_src = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ''
                                attribute_assignments_on_dicts.append((fname, fn.name, line_no, target.value.id, target.attr, line_src))
                elif isinstance(node, ast.AugAssign):
                    target = node.target
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id in dict_vars:
                            line_no = node.lineno
                            line_src = lines[line_no - 1].strip() if 0 <= line_no - 1 < len(lines) else ''
                            attribute_assignments_on_dicts.append((fname, fn.name, line_no, target.value.id, target.attr, line_src))

print(f"Total invalid attribute assignments on dictionaries found: {len(attribute_assignments_on_dicts)}")
for item in attribute_assignments_on_dicts:
    print(f"{item[0]}:{item[2]} in {item[1]}(): {item[3]}.{item[4]} -> {item[5]}")
