import ast
import glob
import os

routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

mutation_methods = {"post", "put", "patch", "delete"}

endpoints = []

for rf in router_files:
    fname = os.path.basename(rf)
    if fname == "__init__.py":
        continue
    with open(rf, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=rf)
    except Exception as e:
        print(f"Failed to parse {fname}: {e}")
        continue

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        
        # Check router decorators
        for dec in node.decorator_list:
            http_method = None
            route_path = None
            if isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute) and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router":
                    http_method = dec.func.attr
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        route_path = dec.args[0].value
            elif isinstance(dec, ast.Attribute):
                if isinstance(dec.value, ast.Name) and dec.value.id == "router":
                    http_method = dec.attr

            if http_method:
                # Check parameters
                args = node.args.args
                defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults
                
                body_params = []
                for arg, default in zip(args, defaults):
                    p_name = arg.arg
                    if p_name in ("self", "cls"):
                        continue
                    p_ann = ast.unparse(arg.annotation) if arg.annotation else None
                    p_def = ast.unparse(default) if default else None
                    
                    # Ignore standard dependencies
                    is_dep = False
                    if p_def:
                        for d in ("Depends", "Query", "Path", "Header", "Cookie", "Security"):
                            if p_def.startswith(d):
                                is_dep = True
                                break
                    if is_dep or p_ann in ("Request", "Response", "BackgroundTasks", "Session"):
                        continue
                    if p_ann and "UploadFile" in p_ann:
                        continue
                        
                    body_params.append({
                        "name": p_name,
                        "annotation": p_ann,
                        "default": p_def
                    })
                
                # Check function body for await request.json()
                has_request_json = "request.json()" in ast.unparse(node)
                
                endpoints.append({
                    "file": fname,
                    "line": node.lineno,
                    "method": http_method.upper(),
                    "path": route_path,
                    "func": node.name,
                    "body_params": body_params,
                    "has_request_json": has_request_json,
                    "ast_node": node
                })

print(f"Total endpoints discovered: {len(endpoints)}")

# Filter to:
# 1. endpoints with dict/Dict/Any/untyped body params
# 2. endpoints with has_request_json
# 3. endpoints with body params that might be non-Pydantic

dict_or_raw_endpoints = []
for ep in endpoints:
    is_target = False
    reasons = []
    if ep["has_request_json"]:
        is_target = True
        reasons.append("has request.json()")
    for p in ep["body_params"]:
        ann = (p["annotation"] or "").lower()
        if not p["annotation"]:
            is_target = True
            reasons.append(f"untyped param '{p['name']}'")
        elif "dict" in ann or ann == "any" or "dict[str, any]" in ann:
            is_target = True
            reasons.append(f"dict-like param '{p['name']}: {p['annotation']}'")
        elif p["name"] in ("payload", "data", "body") and not p["annotation"]:
            is_target = True
            reasons.append(f"raw body param '{p['name']}'")
    if is_target:
        dict_or_raw_endpoints.append((ep, reasons))

print(f"\nFound {len(dict_or_raw_endpoints)} endpoints with dict/untyped/raw body:")
for ep, reasons in dict_or_raw_endpoints:
    print(f"\nFile: {ep['file']}:{ep['line']}")
    print(f"Endpoint: {ep['method']} {ep['path']} -> def {ep['func']}")
    print(f"Reasons: {', '.join(reasons)}")
    print(f"Body params: {ep['body_params']}")
