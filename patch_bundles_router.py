import os
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'bundle.is_active if bundle.is_active is not None',
    'getattr(bundle, "isActive", getattr(bundle, "is_active", None)) if getattr(bundle, "isActive", getattr(bundle, "is_active", None)) is not None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
