import os
import re

filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_rep = content.find('async def _replace_children')
end_rep = content.find('async def findAll', start_rep)
rep_block = content[start_rep:end_rep]

# Insert data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})
rep_block = rep_block.replace('async def _replace_children(self, session, uid: int, data: Dict):\n', 'async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n')
rep_block = rep_block.replace('data.get(', 'data_dict.get(')

content = content[:start_rep] + rep_block + content[end_rep:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
