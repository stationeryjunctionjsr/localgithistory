import os

filepath = 'backend/app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('doc["items"]', 'doc.items')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
