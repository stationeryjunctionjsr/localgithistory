import os
import re

filepath = 'backend/app/repositories/order_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will just regex replace them
content = re.sub(r'\(update_data\.get\("([a-zA-Z0-9_]+)"\)\s*if\s*isinstance\(update_data,\s*dict\)\s*else\s*getattr\(update_data,\s*"([a-zA-Z0-9_]+)",\s*None\)\)', r'getattr(update_data, "\2", None)', content)
content = re.sub(r'\(update_data\.get\("([a-zA-Z0-9_]+)"\)\s*if\s*isinstance\(update_data,\s*dict\)\s*else\s*update_data\.([a-zA-Z0-9_]+)\)', r'update_data.\2', content)

content = re.sub(r'if\s*isinstance\(update_data,\s*dict\):\s*update_data\["([a-zA-Z0-9_]+)"\]\s*=\s*(.+?)\n\s*elif\s*not\s*isinstance\(update_data,\s*dict\):\s*update_data\.([a-zA-Z0-9_]+)\s*=\s*(.+?)\n', r'update_data.\3 = \4\n', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
