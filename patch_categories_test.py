import os

filepath = 'backend/tests/test_categories.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('existing["_id"]', 'existing.id')
content = content.replace('cat_doc["_id"]', 'cat_doc.id')
content = content.replace('cat_doc["name"]', 'cat_doc.name')
content = content.replace('cat_doc["description"]', 'cat_doc.description')
content = content.replace('updated_doc["description"]', 'updated_doc.description')
content = content.replace('updated_doc["isActive"]', 'updated_doc.isActive')
content = content.replace('fetched_doc["_id"]', 'fetched_doc.id')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
