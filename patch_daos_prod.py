import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    unit: Optional[str] = "pc"',
    '''    unit: Optional[str] = "pc"
    tags: Optional[list] = []
    thumbnail: Optional[str] = None
    variantCombinations: Optional[list] = []
    details: Optional[dict] = {}'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
