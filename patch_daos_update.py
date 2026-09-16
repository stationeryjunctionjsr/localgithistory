import os

filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    isReturnable: Optional[bool] = None',
    '''    isReturnable: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
