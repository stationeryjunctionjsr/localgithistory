import os
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'qty = (item.quantity if item.quantity is not None else 1)',
    'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else (item.quantity if item.quantity is not None else 1)'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
