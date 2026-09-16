import os

filepath = 'backend/app/repositories/category_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return await self.storage.update(id, {"isActive": False})',
    'return await self.update(id, {"isActive": False})'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
