import re

with open('backend/app/repositories/cart_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('cart_dict = {"user": cart_data["user"], "items": cart_data.get("items", [])}\n        cart = CartInternalCreate(**cart_dict)', 'cart = CartInternalCreate(user=cart_data["user"], items=cart_data.get("items", []))')

with open('backend/app/repositories/cart_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
