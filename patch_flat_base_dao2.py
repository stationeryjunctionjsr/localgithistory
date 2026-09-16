import os
import re

filepath = 'backend/app/db/mysql_flat_base_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
        merged = {**existing_dict, **update_dict}'''

content = re.sub(
    r'existing_dict = existing.*?merged = \{\*\*existing_dict, \*\*update_dict\}',
    replacement,
    content, flags=re.DOTALL
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
