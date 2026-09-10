import re

with open("backend/app/db/mysql_order_dao.py", 'r', encoding='utf-8') as f:
    content = f.read()

# Replace column list
content = re.sub(r'valet_decline_history,(\s*)shipped_at', r'valet_decline_history, is_urgent_delivery,\1shipped_at', content)

# Replace param list
content = re.sub(r'valet_decline_history,(\s*):shipped_at', r'valet_decline_history, :is_urgent_delivery,\1:shipped_at', content)

with open("backend/app/db/mysql_order_dao.py", 'w', encoding='utf-8') as f:
    f.write(content)
print("Regex replacements successful.")
