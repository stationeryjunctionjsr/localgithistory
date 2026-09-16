import os

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'images=product_data.images if product_data.images is not None else [],',
    'images=product_data.images if product_data.images is not None else [],\n            videos=getattr(product_data, "videos", []),'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
