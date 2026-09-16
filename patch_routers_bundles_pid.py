import os
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'product = await product_repository.findById(item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId)',
    'p_id = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))\n            product = await product_repository.findById(p_id)'
)
content = content.replace(
    'available = await product_repository.get_available_stock(pid, exclude_user_id=user_id)',
    'available = await product_repository.get_available_stock(p_id, exclude_user_id=user_id)'
)
content = content.replace(
    'Product {item.productId} is no longer available',
    'Product {p_id} is no longer available'
)
content = content.replace(
    'product.name is not None else item.productId',
    'product.name is not None else p_id'
)
content = content.replace(
    'available < item.quantity',
    'available < (item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1))'
)
content = content.replace(
    'required: {item.quantity}',
    'required: {item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)}'
)
content = content.replace(
    'pid = item.productId',
    'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else getattr(item, "productId", getattr(item, "product_id", None))'
)
content = content.replace(
    'qty = item.quantity',
    'qty = item.get("quantity", getattr(item, "quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)'
)
content = content.replace(
    'pid = item.get("productId", item.get("product_id")) if isinstance(item, dict) else item.productId\n        qty = item.get("quantity") if isinstance(item, dict) else item.quantity\n        cart_item = CartItem(',
    'cart_item = CartItem('
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
