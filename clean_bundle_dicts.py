import os

filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'bundle_specs = bundle.get("items", []) if isinstance(bundle, dict) else (bundle.items or [])', 
    'bundle_specs = bundle.items or []'
)
content = content.replace(
    'spec_qty = max(1, (spec.get("quantity", 1) if isinstance(spec, dict) else (spec.quantity if spec.quantity is not None else 1)))', 
    'spec_qty = max(1, spec.quantity if spec.quantity is not None else 1)'
)
content = content.replace(
    'spec_pid = str((spec.get("productId") if isinstance(spec, dict) else spec.productId) or "")', 
    'spec_pid = str(spec.productId or "")'
)
content = content.replace(
    'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))', 
    'sales_c = getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
