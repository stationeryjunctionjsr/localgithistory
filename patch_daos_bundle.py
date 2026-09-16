import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    items: Optional[List[BundleItemInternal]] = []',
    '''    items: Optional[List[BundleItemInternal]] = []
    products: Optional[list] = []
    salesCount: Optional[int] = 0'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
