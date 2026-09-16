import os
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'product_repository.get_available_stock(item.productId,',
    'product_repository.get_available_stock(pid,'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
