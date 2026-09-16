import os
import re

filepath = 'backend/app/repositories/user_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''        created_dict = await self.storage.create(user_model)
        from app.models.user import UserResponse
        return UserResponse.model_validate(created_dict) if isinstance(created_dict, dict) else created_dict'''

content = content.replace(
    '        return await self.storage.create(user_model)',
    replacement
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
