import os

filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Clean up users_map
old_users = 'users_map = {str(u.get("id")) if isinstance(u, dict) else str(u.id): u for u in users_list}'
new_users = 'users_map = {str(u.id): u for u in users_list if getattr(u, "id", None)}'
content = content.replace(old_users, new_users)

# Clean up products_map
old_products = 'products_map = {str(p.get("id")) if isinstance(p, dict) else str(p.id): p for p in products_list}'
new_products = 'products_map = {str(p.id): p for p in products_list if getattr(p, "id", None)}'
content = content.replace(old_products, new_products)

# Clean up payments_map
old_payments = """    for p in payments_list:
        if isinstance(p, dict):
            oid = str(p.get("orderId", p.get("order_id")))
        else:
            oid = str(p.orderId) if hasattr(p, "orderId") else str(getattr(p, "order_id", getattr(p, "orderId", None)))
        if oid not in payments_map:
            payments_map[oid] = []
        payments_map[oid].append(p)"""
new_payments = """    for p in payments_list:
        oid = str(getattr(p, "orderId", getattr(p, "order_id", None)))
        if oid not in payments_map:
            payments_map[oid] = []
        payments_map[oid].append(p)"""
content = content.replace(old_payments, new_payments)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
