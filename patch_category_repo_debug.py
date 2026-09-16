import os

filepath = 'backend/app/repositories/category_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '        updates = {**update_dict, "updatedAt": self._get_timestamp()}',
    '        updates = {**update_dict, "updatedAt": self._get_timestamp()}\n        print("UPDATE_DATA:", type(update_data), update_data)\n        print("UPDATES:", updates)'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
