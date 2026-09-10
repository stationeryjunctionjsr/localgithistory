import re

with open("backend/app/db/mysql_order_dao.py", 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'("valetDeclineHistory":.*?else \[\],)',
    r'\1\n            "isUrgentDelivery": bool(getattr(r, "is_urgent_delivery", False)),',
    content,
    flags=re.DOTALL
)

with open("backend/app/db/mysql_order_dao.py", 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied _row_to_doc fix with regex")
