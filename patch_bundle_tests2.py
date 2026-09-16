import os
filepath = 'backend/tests/test_bundle_recommendations.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('b["_id"]', 'b.id')
content = content.replace('b1["_id"]', 'b1.id')
content = content.replace('b2["_id"]', 'b2.id')
content = content.replace('order_response.json().get("_id")', 'order_response.json().get("_id", order_response.json().get("id"))')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
