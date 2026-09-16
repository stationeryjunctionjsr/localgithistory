import os

filepath = 'backend/tests/test_wholesaler_dues.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# user["_id"] -> user.id, user["name"] -> user.name, etc.
content = content.replace('user["_id"]', 'user.id')
content = content.replace('user.get("userId", str(user["_id"]))', 'user.id')
content = content.replace('user["name"]', 'user.name')

# order["_id"] -> order.id
content = content.replace('order["_id"]', 'order.id')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
