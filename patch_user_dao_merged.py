import os
filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
# find instances of merged.something and replace with merged.get("something")
def replace_merged(match):
    attr = match.group(1)
    return f'merged.get("{attr}")'

content = re.sub(r'merged\.([a-zA-Z0-9_]+)', replace_merged, content)
# We also have getattr(merged, 'upiId', None) which is not valid on dict
content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
