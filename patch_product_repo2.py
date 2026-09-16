import os
filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'p.createdAt',
    'p.created_at'
)
content = content.replace(
    'p.updatedAt',
    'p.updated_at'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
