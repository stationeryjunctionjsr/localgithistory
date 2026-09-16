import os
filepath = 'backend/app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    salesCount: Optional[int] = None',
    '    salesCount: Optional[int] = None\n    updatedAt: Optional[str] = None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
