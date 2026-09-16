import os
filepath = 'backend/app/db/mysql_order_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", [])}
        merged = {**existing_dict, **update_dict}'''

content = content.replace(
    'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}',
    replacement
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
