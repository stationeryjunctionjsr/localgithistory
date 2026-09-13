import os
import ast
import json

routers_dir = r"backend/app/routers"
files = sorted([f for f in os.listdir(routers_dir) if f.endswith('.py')])

file_stats = []

for fname in files:
    fpath = os.path.join(routers_dir, fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=fname)
    except Exception as e:
        print(f"Error parsing {fname}: {e}")
        continue

    r_get = 0
    req_get = 0
    env_get = 0
    other_get = 0
    calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            caller = ast.unparse(node.func.value)
            arg_str = ", ".join(ast.unparse(a) for a in node.args)
            if caller in ('router', 'app'):
                r_get += 1
                kind = "router"
            elif caller in ('request.headers', 'request.query_params', 'request.cookies', 'req.headers', 'req.cookies', 'req.query_params', 'request.state'):
                req_get += 1
                kind = "request"
            elif caller in ('os.environ', 'environ'):
                env_get += 1
                kind = "environ"
            else:
                other_get += 1
                kind = "other"
            calls.append({
                "lineno": node.lineno,
                "caller": caller,
                "args": arg_str,
                "kind": kind
            })

    total = r_get + req_get + env_get + other_get
    file_stats.append({
        "file": fname,
        "router_get": r_get,
        "req_get": req_get,
        "env_get": env_get,
        "other_get": other_get,
        "total": total,
        "calls": calls
    })

print(f"{'File':30s} | {'Router.get':10s} | {'Req.get':8s} | {'Env.get':8s} | {'Other.get':10s} | {'Total':6s}")
print("-" * 85)
for s in file_stats:
    print(f"{s['file']:30s} | {s['router_get']:10d} | {s['req_get']:8d} | {s['env_get']:8d} | {s['other_get']:10d} | {s['total']:6d}")

print("-" * 85)
total_r = sum(s['router_get'] for s in file_stats)
total_req = sum(s['req_get'] for s in file_stats)
total_env = sum(s['env_get'] for s in file_stats)
total_oth = sum(s['other_get'] for s in file_stats)
total_all = sum(s['total'] for s in file_stats)
print(f"{'TOTAL (' + str(len(file_stats)) + ' files)':30s} | {total_r:10d} | {total_req:8d} | {total_env:8d} | {total_oth:10d} | {total_all:6d}")
