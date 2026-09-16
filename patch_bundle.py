import os

filepath = 'backend/tests/test_bundle_recommendations.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('p1["_id"]', 'p1.id')
content = content.replace('p2["_id"]', 'p2.id')
content = content.replace('bundle["_id"]', 'bundle.id')
content = content.replace('order["_id"]', 'order.id')
content = content.replace('user["_id"]', 'user.id')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
