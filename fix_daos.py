import re

with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = re.sub(r'if "([^"]+)" in data:', r'if hasattr(data, "\g<1>") and getattr(data, "\g<1>") is not None:', content)
new_content = re.sub(r'if "([^"]+)" in merged:', r'if hasattr(merged, "\g<1>") and getattr(merged, "\g<1>") is not None:', new_content)
new_content = new_content.replace('data.model_dump(exclude_unset=True)', 'data')

with open('backend/app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed mysql_flat_daos.py")