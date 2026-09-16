import os
filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'merged = {**existing, **update_data}',
    'existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})\n        update_dict = update_data if isinstance(update_data, dict) else getattr(update_data, "__dict__", {})\n        merged = {**existing_dict, **update_dict}'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
