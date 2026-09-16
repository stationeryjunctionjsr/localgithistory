import os
filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    isActive: Optional[bool] = None',
    '    isActive: Optional[bool] = None\n    salesCount: Optional[int] = None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
