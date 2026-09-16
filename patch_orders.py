import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return product.seller_id',
    'return getattr(product, "seller_id", None)'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
