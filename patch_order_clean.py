import os
import re

filepath = 'backend/app/db/mysql_order_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace merged logic
replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
        merged = {**existing_dict, **update_dict}'''
content = content.replace('        merged = {**existing, **update_data}', replacement_merged)

# Replace update_data.<attr> with merged.get('<attr>') in the parameters
def replace_attr(match):
    return f'merged.get("{match.group(1)}")'
content = re.sub(r'update_data\.([a-zA-Z0-9_]+)', replace_attr, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
