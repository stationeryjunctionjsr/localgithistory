import re

with open('backend/app/repositories/brand_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

create_replace = '''        from app.models.daos import BrandInternalCreate
        internal_data = BrandInternalCreate(
            name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
            description=getattr(data, 'description', data.get('description') if isinstance(data, dict) else None),
            isActive=getattr(data, 'isActive', data.get('isActive') if isinstance(data, dict) else True)
        )'''

content = re.sub(r'        from app\.models\.daos import BrandInternalCreate\n        if isinstance\(data, dict\):\n.*?BrandInternalCreate\(\*\*data\.model_dump\(exclude_unset=True\)\)', create_replace, content, flags=re.DOTALL)

update_replace = '''        from app.models.daos import BrandInternalUpdate
        internal_update = BrandInternalUpdate()
        
        if isinstance(update_data, dict):
            if 'name' in update_data: internal_update.name = update_data['name']
            if 'description' in update_data: internal_update.description = update_data['description']
            if 'isActive' in update_data: internal_update.isActive = update_data['isActive']
        else:
            if 'name' in update_data.model_fields_set: internal_update.name = update_data.name
            if 'description' in update_data.model_fields_set: internal_update.description = update_data.description
            if 'isActive' in update_data.model_fields_set: internal_update.isActive = update_data.isActive'''

content = re.sub(r'        from app\.models\.daos import BrandInternalUpdate\n        if isinstance\(update_data, dict\):\n.*?BrandInternalUpdate\(\*\*update_data\.model_dump\(exclude_unset=True\)\)', update_replace, content, flags=re.DOTALL)

with open('backend/app/repositories/brand_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
