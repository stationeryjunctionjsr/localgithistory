import os
import re

filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace merged logic
replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
        merged = {**existing_dict, **update_dict}'''
content = content.replace('        merged = {**existing, **update_data}', replacement_merged)

# Replace merged.<attr> with merged.get('<attr>') in the parameters
def replace_attr(match):
    return f'merged.get("{match.group(1)}")'
content = re.sub(r'merged\.([a-zA-Z0-9_]+)', replace_attr, content)

# Fix getattr(merged, ...)
content = content.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
content = content.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")

# Fix boolean logic
content = content.replace(
    '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
    '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
)
content = content.replace(
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
)

# In _replace_children, data is merged, so it is a dict. Replace data.<attr> with data.get("<attr>")
# Only in _replace_children block
start_idx = content.find('async def _replace_children')
end_idx = content.find('async def delete', start_idx)
sub_content = content[start_idx:end_idx]

sub_content = re.sub(r'data\.([a-zA-Z0-9_]+)', replace_attr, sub_content) # Actually replace_data_attr
sub_content = sub_content.replace('merged.get("', 'data.get("')

content = content[:start_idx] + sub_content + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
