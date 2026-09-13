import glob
import importlib
import inspect
import os
import sys

BACKEND_DIR = os.path.abspath("backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["JWT_SECRET_KEY"] = "dummy_secret_for_audit"

from pydantic import BaseModel

ROUTERS_DIR = os.path.join(BACKEND_DIR, "app", "routers")

def audit_router_inline_models():
    print("=== Auditing Inline Pydantic Models Across All Router Files ===")
    router_files = sorted(glob.glob(os.path.join(ROUTERS_DIR, "*.py")))
    
    total_inline_models = 0
    total_inline_fields = 0
    empty_inline = []
    untyped_inline = []
    inline_summary = []

    for rpath in router_files:
        mod_name = os.path.splitext(os.path.basename(rpath))[0]
        try:
            mod = importlib.import_module(f"app.routers.{mod_name}")
        except Exception as e:
            print(f"Error importing {mod_name}: {e}")
            continue

        for name, obj in inspect.getmembers(mod, inspect.isclass):
            # Must be defined directly in this module, not imported
            if issubclass(obj, BaseModel) and obj is not BaseModel and obj.__module__ == mod.__name__:
                total_inline_models += 1
                fields = obj.model_fields
                if not fields:
                    empty_inline.append((mod_name, name))
                else:
                    total_inline_fields += len(fields)
                    inline_summary.append((mod_name, name, len(fields), list(fields.keys())))
                    for fname, f_info in fields.items():
                        if f_info.annotation is None:
                            untyped_inline.append((mod_name, name, fname))

    print(f"Total inline BaseModel subclasses discovered: {total_inline_models}")
    print(f"Total fields across inline models: {total_inline_fields}")
    print(f"Empty inline models: {len(empty_inline)} -> {empty_inline}")
    print(f"Untyped fields: {len(untyped_inline)} -> {untyped_inline}")
    print("\nSample inline models defined:")
    for mod, name, num_f, fnames in inline_summary[:10]:
        print(f"  [{mod}] {name} ({num_f} fields): {fnames}")

if __name__ == "__main__":
    audit_router_inline_models()
