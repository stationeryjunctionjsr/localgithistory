import os
filepath = 'backend/app/repositories/bundle_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if any(i.productId == product_id for i in items):',
    'if any(getattr(i, "productId", i.get("productId", i.get("product_id")) if isinstance(i, dict) else getattr(i, "product_id", None)) == product_id for i in items):'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
