import re

with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Revert b	merged = ...(**{**existing, **data}) back to existing.model_dump()
content = re.sub(r'\(\**\{\**existing, \**data\}\)', r'(**{0z**existing.model_dump(by_alias=True), **data.model_dump(exclude_unset=True)})', content)

with open('backend/app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed merged unpacking')
