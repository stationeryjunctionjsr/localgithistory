import os

filepath = 'backend/app/models/product.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    mrp: Optional[float] = None',
    '''    mrp: Optional[float] = None
    gst: Optional[float] = None'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
