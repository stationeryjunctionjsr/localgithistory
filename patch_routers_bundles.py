import os
import re
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'product = await product_repository.findById(item.productId)',
    'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)'
)
content = content.replace(
    'cart_item = CartItem(',
    'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem('
)
content = content.replace(
    'productId=item.productId,',
    'productId=pid,'
)
content = content.replace(
    'quantity=item.quantity,',
    'quantity=qty,'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
