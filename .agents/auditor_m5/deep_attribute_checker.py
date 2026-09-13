import ast
import glob
import importlib
import inspect
import os
import sys
from typing import Dict, Any, List, Set

BACKEND_DIR = os.path.abspath("backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["JWT_SECRET_KEY"] = "dummy_secret_for_audit"

from pydantic import BaseModel
import app.models.schemas as schemas_module

ROUTERS_DIR = os.path.join(BACKEND_DIR, "app", "routers")

# Discover all Pydantic models in schemas.py
SCHEMA_MODELS: Dict[str, Any] = {}
for name, obj in inspect.getmembers(schemas_module, inspect.isclass):
    if issubclass(obj, BaseModel):
        SCHEMA_MODELS[name] = obj

print(f"Total Pydantic models discovered in schemas.py: {len(SCHEMA_MODELS)}")

def analyze_router(router_path: str):
    mod_name = os.path.splitext(os.path.basename(router_path))[0]
    with open(router_path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src, filename=router_path)
    
    # Import the module to get runtime types
    try:
        mod = importlib.import_module(f"app.routers.{mod_name}")
    except Exception as e:
        return {"error": f"Import error: {e}"}

    # Discover inline models
    inline_models = {}
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, BaseModel):
            inline_models[name] = obj

    results = {
        "module": mod_name,
        "endpoints": 0,
        "payload_params": [],
        "attribute_accesses": [],
        "invalid_attributes": [],
        "subscript_accesses": [],
        "get_calls_on_payload": [],
    }

    # Find endpoint functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_endpoint = False
            for dec in node.decorator_list:
                dec_str = ast.unparse(dec)
                if any(m in dec_str for m in ["router.get", "router.post", "router.put", "router.patch", "router.delete", "router.api_route"]):
                    is_endpoint = True
                    break
            
            if is_endpoint:
                results["endpoints"] += 1
                
                # Check parameters for Pydantic models
                # Map param_name -> model_class
                param_models = {}
                for arg in node.args.args:
                    if arg.annotation:
                        ann_str = ast.unparse(arg.annotation)
                        # Look up class in inline_models or SCHEMA_MODELS or getattr(mod, ann_str, None)
                        cls = inline_models.get(ann_str) or SCHEMA_MODELS.get(ann_str) or getattr(mod, ann_str, None)
                        if cls and inspect.isclass(cls) and issubclass(cls, BaseModel):
                            param_models[arg.arg] = cls
                            results["payload_params"].append((arg.arg, ann_str))

                # Now inspect the function body for accesses to param_models
                for child in ast.walk(node):
                    # Check attribute access
                    if isinstance(child, ast.Attribute):
                        val_str = ast.unparse(child.value)
                        if val_str in param_models:
                            attr = child.attr
                            cls = param_models[val_str]
                            results["attribute_accesses"].append((val_str, attr, cls.__name__))
                            
                            # Check if attr is on cls
                            has_field = (
                                attr in cls.model_fields
                                or hasattr(cls, attr)
                                or attr in getattr(cls, "__annotations__", {})
                            )
                            if not has_field:
                                # Also check if alias matches
                                has_alias = any(getattr(f, 'alias', None) == attr for f in cls.model_fields.values())
                                if not has_alias:
                                    results["invalid_attributes"].append((node.name, val_str, attr, cls.__name__, child.lineno))

                    # Check subscript access payload['key']
                    elif isinstance(child, ast.Subscript):
                        val_str = ast.unparse(child.value)
                        if val_str in param_models:
                            results["subscript_accesses"].append((node.name, val_str, ast.unparse(child.slice), child.lineno))

                    # Check .get() calls
                    elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "get":
                        val_str = ast.unparse(child.func.value)
                        if val_str in param_models:
                            results["get_calls_on_payload"].append((node.name, val_str, child.lineno))

    return results

def main():
    print("=== Analyzing All Router Endpoint Parameter Types & Dot-Notation Access ===")
    router_files = sorted(glob.glob(os.path.join(ROUTERS_DIR, "*.py")))
    
    total_endpoints = 0
    total_payload_params = 0
    total_attrs = 0
    total_invalid_attrs = 0
    total_subscripts = 0
    total_payload_gets = 0

    invalid_attr_list = []
    subscript_list = []
    payload_get_list = []

    for rpath in router_files:
        res = analyze_router(rpath)
        if "error" in res:
            print(f"Error in {os.path.basename(rpath)}: {res['error']}")
            continue
        
        total_endpoints += res["endpoints"]
        total_payload_params += len(res["payload_params"])
        total_attrs += len(res["attribute_accesses"])
        total_invalid_attrs += len(res["invalid_attributes"])
        total_subscripts += len(res["subscript_accesses"])
        total_payload_gets += len(res["get_calls_on_payload"])

        for item in res["invalid_attributes"]:
            invalid_attr_list.append((res["module"], item))
        for item in res["subscript_accesses"]:
            subscript_list.append((res["module"], item))
        for item in res["get_calls_on_payload"]:
            payload_get_list.append((res["module"], item))

    print(f"Total Router Modules: {len(router_files)}")
    print(f"Total Route Endpoints: {total_endpoints}")
    print(f"Total Pydantic Model Payload Parameters: {total_payload_params}")
    print(f"Total Dot-Notation Attribute Accesses on Payloads: {total_attrs}")
    print(f"Invalid Attributes on Model: {total_invalid_attrs}")
    print(f"Subscript Accesses on Payloads (payload['x']): {total_subscripts}")
    print(f".get() Calls on Payloads: {total_payload_gets}")

    if invalid_attr_list:
        print("\n--- Invalid Attributes Found ---")
        for mod, item in invalid_attr_list:
            print(f"  [{mod}] {item}")

    if subscript_list:
        print("\n--- Subscript Accesses Found ---")
        for mod, item in subscript_list:
            print(f"  [{mod}] {item}")

    if payload_get_list:
        print("\n--- .get() Calls Found on Payloads ---")
        for mod, item in payload_get_list:
            print(f"  [{mod}] {item}")

if __name__ == "__main__":
    main()
