import os
filepath = 'backend/app/db/mysql_flat_daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'q = f"UPDATE stock_reservations SET {set_clause} WHERE id = :id"',
    'q = f"UPDATE {self.TABLE} SET {set_clause} WHERE id = :id"'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
