import os
filepath = 'backend/app/db/mysql_user_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '\'is_email_verified\': 1 if (merged.get("isEmailVerified") if merged.get("isEmailVerified") is not None else False) else None',
    '\'is_email_verified\': 1 if merged.get("isEmailVerified") else 0'
)
content = content.replace(
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else None',
    '\'is_active\': 1 if (merged.get("isActive") if merged.get("isActive") is not None else True) else 0'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
