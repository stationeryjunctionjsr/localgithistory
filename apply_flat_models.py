import re

with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = "from app.models.daos_flat import *\n" + content

classes = re.findall(r'class (MySQL[a-zA-Z0-9_]+DAO):', content)
for cls in classes:
    entity = cls.replace('MySQL', '').replace('DAO', '')
    
    # Update create signature
    create_pattern = r'(class ' + cls + r':.*?async def create\(self, data: )Dict(\) ->)'
    content = re.sub(create_pattern, r'\1' + f'{entity}InternalCreate' + r'\2', content, flags=re.DOTALL)
    
    # Update update signature and merged object instantiation
    update_pattern = r'(class ' + cls + r':.*?async def update\(self, id: str, data: )Dict(\) -> Optional\[.*?\]:.*?merged = ){\*\*existing, \*\*data}'
    replacement = r'\1' + f'{entity}InternalUpdate' + r'\2' + f'{entity}InternalUpdate(**{{**existing, **data}})'
    content = re.sub(update_pattern, replacement, content, flags=re.DOTALL)
    
with open('backend/app/db/mysql_flat_daos.py', 'w', encoding='utf-8') as f:
    f.write(content)
