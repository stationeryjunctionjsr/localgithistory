import os
filepath = 'backend/app/routers/bundles.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return {"bundles": enriched}',
    'return enriched'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
