import re

with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('**data}', '**data.model_dump(exclude_unset=True)}')

with open('backend/app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(content)
