import os
import re

filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace merged logic in update
replacement_merged = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
        merged = {**existing_dict, **update_dict}'''
content = content.replace('        merged = {**existing, **update_data}', replacement_merged)

# 2. Patch ONLY the UPDATE sql parameter mapping to use merged.get() instead of merged.<attr>
# We can find the block inside update(self, id...): 
# from sync with factory() as session: to wait self._replace_children
start_update = content.find('async with factory() as session:', content.find('async def update'))
end_update = content.find('await self._replace_children', start_update)
update_block = content[start_update:end_update]
def replace_merged_attr(match):
    return f'merged.get("{match.group(1)}")'
update_block = re.sub(r'merged\.([a-zA-Z0-9_]+)', replace_merged_attr, update_block)
update_block = update_block.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
update_block = update_block.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
update_block = update_block.replace(
    '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
    '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
)
update_block = update_block.replace(
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
)
content = content[:start_update] + update_block + content[end_update:]

# 3. Patch _replace_children block to use data.get() instead of data.<attr>
start_rep = content.find('async def _replace_children')
end_rep = content.find('async def findAll', start_rep)
rep_block = content[start_rep:end_rep]
def replace_data_attr(match):
    return f'data.get("{match.group(1)}")'
rep_block = re.sub(r'data\.([a-zA-Z0-9_]+)', replace_data_attr, rep_block)
content = content[:start_rep] + rep_block + content[end_rep:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
