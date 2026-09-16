import os
import re

filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Update update() method
in_update = False
for i, line in enumerate(lines):
    if 'async def update(self, id: str, update_data: Dict) -> Optional[Dict]:' in line:
        in_update = True
    
    if in_update:
        if 'merged = {**existing, **update_data}' in line:
            lines[i] = '''        existing_dict = existing if isinstance(existing, dict) else getattr(existing, "__dict__", {})
        if isinstance(update_data, dict):
            update_dict = update_data
        else:
            update_dict = {k: getattr(update_data, k) for k in getattr(update_data, "model_fields_set", getattr(update_data, "__dict__", {}))}
        merged = {**existing_dict, **update_dict}\n'''
        
        # Replace merged.something with merged.get("something") in the UPDATE query parameters
        if 'WHERE id = :id' in line or 'merged.' in line or 'merged,' in line:
            # We must be careful not to break other things.
            line = re.sub(r'merged\.([a-zA-Z0-9_]+)', r'merged.get("\1")', line)
            line = line.replace("getattr(merged, 'upiId', None)", "merged.get('upiId')")
            line = line.replace("getattr(merged, 'qrCodeUrl', None)", "merged.get('qrCodeUrl')")
            line = line.replace(
                '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
                '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
            )
            line = line.replace(
                '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
                '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
            )
            lines[i] = line
        
        if 'async def delete' in line:
            in_update = False


# 2. Update _replace_children() method
in_rep = False
for i, line in enumerate(lines):
    if 'async def _replace_children(self, session, uid: int, data: Dict):' in line:
        in_rep = True
        lines[i] = '    async def _replace_children(self, session, uid: int, data):\n        data_dict = data if isinstance(data, dict) else getattr(data, "__dict__", {})\n'
        continue
    
    if in_rep:
        if 'async def ' in line:
            in_rep = False
            continue
        
        lines[i] = re.sub(r'data\.([a-zA-Z0-9_]+)', r'data_dict.get("\1")', line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)
