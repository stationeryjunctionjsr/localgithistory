import os

filepath = 'backend/app/repositories/user_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from app.models.user import UserResponse', 'from app.models.schemas import UserResponse')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
