import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    stock: Optional[int] = 0',
    '''    stock: Optional[int] = 0
    unit: Optional[str] = "pc"'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
