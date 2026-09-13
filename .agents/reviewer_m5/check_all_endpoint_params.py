import ast
import glob
import os

routers_dir = 'backend/app/routers'
router_files = sorted(glob.glob(os.path.join(routers_dir, '*.py')))

ROUTE_DECORATORS = {'get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'api_route'}

total_endpoints = 0
endpoints_with_body = 0
body_params = []

for fpath in router_files:
    fname = os.path.basename(fpath)
    if fname == '__init__.py':
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        src = f.read()
    tree = ast.parse(src, filename=fpath)
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_route = False
            route_method = None
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ROUTE_DECORATORS:
                    is_route = True
                    route_method = dec.func.attr
                    break
            
            if is_route:
                total_endpoints += 1
                for arg in node.args.args:
                    arg_name = arg.arg
                    # Skip common framework arguments
                    if arg_name in ('request', 'response', 'background_tasks'):
                        continue
                    num_defaults = len(node.args.defaults)
                    pos = node.args.args.index(arg)
                    default_idx = pos - (len(node.args.args) - num_defaults)
                    default_str = ""
                    if default_idx >= 0:
                        default_str = ast.unparse(node.args.defaults[default_idx])
                    
                    if "Depends" in default_str or "Header" in default_str or "Query" in default_str or "Path" in default_str or "Security" in default_str:
                        continue
                    
                    ann_str = ast.unparse(arg.annotation) if arg.annotation else "None"
                    body_params.append((fname, node.name, route_method, arg_name, ann_str, default_str))

print(f"Total route endpoints identified: {total_endpoints}")
print(f"Total non-dependency/header parameters: {len(body_params)}")

suspicious = []
for fname, fn_name, method, arg, ann, default in body_params:
    ann_lower = ann.lower()
    if 'dict' in ann_lower or ann_lower in ('any', 'none') or not ann:
        suspicious.append((fname, fn_name, method, arg, ann, default))

print(f"Suspicious / untyped body parameters: {len(suspicious)}")
for s in suspicious:
    print(" ", s)
