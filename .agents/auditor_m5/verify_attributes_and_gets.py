import ast
import glob
import importlib
import inspect
import os
import sys

BACKEND_DIR = os.path.abspath("backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["JWT_SECRET_KEY"] = "dummy_secret_for_audit_inspection"

from pydantic import BaseModel

ROUTERS_DIR = os.path.join(BACKEND_DIR, "app", "routers")

EXEMPT_CALLERS = {
    "router", "app", "request", "headers", "os", "environ",
    "product_map", "products_map", "users_map", "payments_map", "order_map",
    "valets_map", "sellers_map", "seller_docs", "seller_delivery_map",
    "avail_map", "cache", "_guest_rec_cache", "_cart_products_map",
    "returned_items_qty", "min_versions", "_session_last_touch",
    "params", "query_params"
}

def get_all_gets_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    
    gets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            caller_name = None
            if isinstance(node.func.value, ast.Name):
                caller_name = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                caller_name = node.func.value.attr
                # check parent too e.g. request.headers.get
                if isinstance(node.func.value.value, ast.Name):
                    caller_name = f"{node.func.value.value.id}.{caller_name}"
            
            # Check arguments
            first_arg = None
            if node.args:
                if isinstance(node.args[0], ast.Constant):
                    first_arg = node.args[0].value
                elif isinstance(node.args[0], ast.Name):
                    first_arg = node.args[0].id
            
            gets.append({
                "line": node.lineno,
                "caller": caller_name,
                "first_arg": first_arg,
                "raw": ast.unparse(node)
            })
    return gets

def main():
    print("=== Checking All .get() Calls Across All Routers ===")
    router_files = sorted(glob.glob(os.path.join(ROUTERS_DIR, "*.py")))
    
    total_gets = 0
    non_exempt_gets = []
    
    for rpath in router_files:
        fname = os.path.basename(rpath)
        gets = get_all_gets_in_file(rpath)
        total_gets += len(gets)
        
        for g in gets:
            caller = g["caller"] or ""
            # Check exemption
            is_exempt = False
            for exempt in EXEMPT_CALLERS:
                if caller == exempt or caller.endswith(f".{exempt}") or exempt in caller.split('.'):
                    is_exempt = True
                    break
            
            # Check if caller is request.headers or similar
            if "headers" in caller or "query" in caller or "cookies" in caller or "environ" in caller or "state" in caller:
                is_exempt = True
            
            if not is_exempt:
                non_exempt_gets.append((fname, g))
    
    print(f"Total .get() calls found across all {len(router_files)} routers: {total_gets}")
    print(f"Non-exempt .get() calls found: {len(non_exempt_gets)}")
    for fname, g in non_exempt_gets:
        print(f"  [{fname}:{g['line']}] Caller: '{g['caller']}', Arg: '{g['first_arg']}' -> {g['raw']}")

if __name__ == "__main__":
    main()
