import inspect
import os
import sys
from typing import get_type_hints

BACKEND_DIR = os.path.abspath("backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["JWT_SECRET_KEY"] = "dummy_secret_for_audit"

from pydantic import BaseModel
import app.models.schemas as schemas

def audit_models():
    print("=== Auditing Pydantic Models in schemas.py ===")
    
    empty_models = []
    models_audited = 0
    total_fields = 0
    untyped_fields = []

    for name, obj in inspect.getmembers(schemas, inspect.isclass):
        if issubclass(obj, BaseModel) and obj is not BaseModel:
            models_audited += 1
            fields = obj.model_fields
            if not fields:
                # Some empty models might be marker classes or error responses
                empty_models.append(name)
            else:
                total_fields += len(fields)
                for fname, f_info in fields.items():
                    if f_info.annotation is None:
                        untyped_fields.append((name, fname))

    print(f"Total BaseModel subclasses audited: {models_audited}")
    print(f"Total fields across models: {total_fields}")
    print(f"Empty models (0 fields): {len(empty_models)} -> {empty_models}")
    print(f"Untyped fields: {len(untyped_fields)} -> {untyped_fields}")

if __name__ == "__main__":
    audit_models()
