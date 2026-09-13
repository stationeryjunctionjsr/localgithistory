import ast
import glob
import os
import sys

# Scan all router files in backend/app/routers/
routers_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routers")
router_files = sorted(glob.glob(os.path.join(routers_dir, "*.py")))

print(f"Found {len(router_files)} router files in {routers_dir}")

class EndpointVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.endpoints = []
        
    def visit_FunctionDef(self, node):
        self._check_endpoint(node)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self._check_endpoint(node)
        self.generic_visit(node)
        
    def _check_endpoint(self, node):
        # Check if decorated with @router.<method>
        is_router_endpoint = False
        http_method = None
        route_path = None
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "router":
                    is_router_endpoint = True
                    http_method = func.attr
                    if decorator.args:
                        arg0 = decorator.args[0]
                        if isinstance(arg0, ast.Constant):
                            route_path = arg0.value
            elif isinstance(decorator, ast.Attribute):
                if isinstance(decorator.value, ast.Name) and decorator.value.id == "router":
                    is_router_endpoint = True
                    http_method = decorator.attr
                    
        if not is_router_endpoint:
            return
            
        endpoint_info = {
            "func_name": node.name,
            "lineno": node.lineno,
            "http_method": http_method,
            "route_path": route_path,
            "params": [],
            "dict_params": [],
            "node": node
        }
        
        # Analyze parameters
        # FastApi default args mapping
        args = node.args.args
        defaults = [None] * (len(args) - len(node.args.defaults)) + node.args.defaults
        
        for arg, default in zip(args, defaults):
            param_name = arg.arg
            if param_name in ("self", "cls"):
                continue
                
            ann_str = ast.unparse(arg.annotation) if arg.annotation else None
            default_str = ast.unparse(default) if default else None
            
            is_fastapi_dependency = False
            if default_str:
                for dep_name in ("Depends", "Query", "Path", "Header", "Cookie", "Security"):
                    if default_str.startswith(dep_name):
                        is_fastapi_dependency = True
                        break
                        
            is_special = False
            if ann_str in ("Request", "Response", "BackgroundTasks", "Session", "UploadFile"):
                is_special = True
            if ann_str and "UploadFile" in ann_str:
                is_special = True
                
            # Check if this is a dict or untyped payload
            is_dict_like = False
            if not is_fastapi_dependency and not is_special:
                if ann_str:
                    ann_lower = ann_str.lower()
                    if "dict" in ann_lower or ann_str == "Any" or "dict[str, any]" in ann_lower:
                        is_dict_like = True
                else:
                    # Untyped param
                    if default_str is None or "Body" in default_str:
                        is_dict_like = True
                    elif param_name in ("payload", "data", "body", "item", "req"):
                        is_dict_like = True
                        
            param_info = {
                "name": param_name,
                "annotation": ann_str,
                "default": default_str,
                "is_dict_like": is_dict_like,
                "is_fastapi_dependency": is_fastapi_dependency,
                "is_special": is_special
            }
            endpoint_info["params"].append(param_info)
            if is_dict_like:
                endpoint_info["dict_params"].append(param_info)
                
        self.endpoints.append(endpoint_info)

results = []
for rf in router_files:
    fname = os.path.basename(rf)
    with open(rf, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=rf)
        except Exception as e:
            print(f"Error parsing {fname}: {e}")
            continue
    visitor = EndpointVisitor(fname)
    visitor.visit(tree)
    if visitor.endpoints:
        results.append((fname, visitor.endpoints))

print(f"\nTotal router files with endpoints: {len(results)}")
dict_endpoint_count = 0
for fname, endpoints in results:
    dict_endpoints = [ep for ep in endpoints if ep["dict_params"]]
    if dict_endpoints:
        print(f"\n=== {fname} ({len(dict_endpoints)} endpoints with dict/untyped body) ===")
        for ep in dict_endpoints:
            dict_endpoint_count += 1
            dict_param_names = [p["name"] + (f": {p['annotation']}" if p["annotation"] else " (untyped)") for p in ep["dict_params"]]
            print(f"  Line {ep['lineno']}: {ep['http_method'].upper()} {ep['route_path']} -> def {ep['func_name']} params: {', '.join(dict_param_names)}")

print(f"\nTotal endpoints with dict/untyped body: {dict_endpoint_count}")
