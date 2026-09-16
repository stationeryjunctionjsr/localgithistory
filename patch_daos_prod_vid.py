import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    details: Optional[dict] = {}',
    '''    details: Optional[dict] = {}
    videos: Optional[list] = []'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
