import ast
import glob
import os

routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

all_param_types = set()
body_params_by_type = {}

for rf in router_files:
    fname = os.path.basename(rf)
    if fname == "__init__.py":
        continue
    with open(rf, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=rf)
    except Exception as e:
        continue

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        
        is_endpoint = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router":
                    is_endpoint = True
            elif isinstance(dec, ast.Attribute) and isinstance(dec.value, ast.Name) and dec.value.id == "router":
                is_endpoint = True
                
        if not is_endpoint:
            continue
            
        args = node.args.args
        defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults
        for arg, default in zip(args, defaults):
            p_name = arg.arg
            if p_name in ("self", "cls"):
                continue
            p_ann = ast.unparse(arg.annotation) if arg.annotation else "NONE"
            p_def = ast.unparse(default) if default else "NONE"
            
            # check if dependency or path/query
            is_dep = False
            for d in ("Depends", "Query", "Path", "Header", "Cookie", "Security"):
                if p_def.startswith(d):
                    is_dep = True
                    break
            if is_dep:
                continue
            if p_ann in ("Request", "Response", "BackgroundTasks", "Session"):
                continue
            if "UploadFile" in p_ann:
                continue
                
            # Path parameters like `order_id: str`, `user_id: str`, `id: str`
            # Let's record this
            entry = f"{fname}:{node.lineno} def {node.name}({p_name}: {p_ann} = {p_def})"
            body_params_by_type.setdefault(p_ann, []).append(entry)

print("=== ALL PARAMETER TYPES FOR NON-DEPENDENCY PARAMETERS ===")
for p_ann, occurrences in sorted(body_params_by_type.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\nType: {p_ann} ({len(occurrences)} occurrences)")
    for oc in occurrences[:4]:
        print(f"  {oc}")
    if len(occurrences) > 4:
        print(f"  ... and {len(occurrences) - 4} more")
