import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    unit: Optional[str] = "pc"',
    '''    productId: Optional[int] = None
    productIdFormatted: Optional[str] = None
    unit: Optional[str] = "pc"'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
