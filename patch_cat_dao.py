import os

filepath = 'backend/app/db/mysql_category_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'existing_dict = existing.__dict__',
    'existing_dict = existing.model_dump(by_alias=True)'
)
content = content.replace(
    'update_dict = update_data.__dict__',
    'update_dict = update_data.model_dump(exclude_unset=True)'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
