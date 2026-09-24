import re

with open('app/db/mysql_notifications_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('if data.data is not None:', 'if getattr(data, "metadata", getattr(data, "data", None)) is not None:')
text = text.replace('child_list = data.data or []', 'child_list = getattr(data, "metadata", getattr(data, "data", None)) or {}')
text = text.replace('for k, v in child_list.items():', 'child_dict = child_list.model_dump() if hasattr(child_list, "model_dump") else child_list\n            for k, v in (child_dict.items() if isinstance(child_dict, dict) else []):')

with open('app/db/mysql_notifications_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
