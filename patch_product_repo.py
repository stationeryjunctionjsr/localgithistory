import os
filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'p.isActive if p.isActive is not None else True',
    'p.is_active if p.is_active is not None else True'
)
content = content.replace(
    'if (p.isActive if',
    'if (p.is_active if'
)
content = content.replace(
    'p.isActive',
    'p.is_active'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
