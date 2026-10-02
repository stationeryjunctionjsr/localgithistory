import re

file_path = "app/db/mysql_product_dao.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("s_status = getattr(seller, 'request_status', getattr(seller, 'requestStatus', 'pending'))\n", "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Removed extra s_status line")
