import os
filepath = 'backend/app/db/mysql_order_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
def replace_update_data(match):
    attr = match.group(1)
    return f'(update_data.get("{attr}") if isinstance(update_data, dict) else update_data.{attr})'

content = re.sub(r'update_data\.([a-zA-Z0-9_]+)', replace_update_data, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
