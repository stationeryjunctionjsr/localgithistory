import os
import ast
import json

routers_dir = r"backend/app/routers"
files = sorted([f for f in os.listdir(routers_dir) if f.endswith('.py')])

all_calls = []

for fname in files:
    fpath = os.path.join(routers_dir, fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=fname)
    except Exception as e:
        print(f"Error parsing {fname}: {e}")
        continue

    # Find parent functions and their arguments
    func_info = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            func_info[node.name] = {
                "start": node.lineno,
                "end": getattr(node, 'end_lineno', node.lineno),
                "args": args
            }

    def get_enclosing_func(lineno):
        matching = [name for name, info in func_info.items() if info["start"] <= lineno <= info["end"]]
        return matching[-1] if matching else "<module>"

    lines = src.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            caller = ast.unparse(node.func.value)
            arg_str = ", ".join(ast.unparse(a) for a in node.args)
            lineno = node.lineno
            line_str = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            func_name = get_enclosing_func(lineno)

            all_calls.append({
                "file": fname,
                "lineno": lineno,
                "caller": caller,
                "args": arg_str,
                "func": func_name,
                "line_str": line_str
            })

with open("c:/Ecommerce app/.agents/explorer_survey_2/raw_calls.json", "w", encoding="utf-8") as out:
    json.dump(all_calls, out, indent=2)

print(f"Dumped {len(all_calls)} calls to raw_calls.json")
