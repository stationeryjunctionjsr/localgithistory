import os

filepath = 'backend/tests/test_bundle_recommendations.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('p["_id"]', 'p.id')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
