import os
import re

filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I need to change data.address, data.savedAddresses, etc. in _replace_children
def replace_data_attr(match):
    attr = match.group(1)
    return f'data.get("{attr}")'

# First isolate _replace_children function block roughly
# It starts at def _replace_children and goes up to async def delete
start_idx = content.find('async def _replace_children')
end_idx = content.find('async def delete', start_idx)
sub_content = content[start_idx:end_idx]

sub_content = re.sub(r'data\.([a-zA-Z0-9_]+)', replace_data_attr, sub_content)

content = content[:start_idx] + sub_content + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
