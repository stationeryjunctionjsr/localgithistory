import glob
import re
import ast

def get_model_fields(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    models = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and 'Internal' in node.name:
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    fields.append(item.target.id)
            models[node.name] = fields
    return models

models = {**get_model_fields('backend/app/models/daos.py'), **get_model_fields('backend/app/models/daos_flat.py'), **get_model_fields('backend/app/models/schemas.py')}

files = [
    'backend/app/repositories/banner_repository.py',
    'backend/app/repositories/brand_repository.py',
    'backend/app/repositories/bundle_repository.py',
    'backend/app/repositories/cart_repository.py',
    'backend/app/repositories/category_repository.py',
    'backend/app/repositories/payment_repository.py',
    'backend/app/repositories/seller_request_repository.py',
    'backend/app/repositories/session_repository.py',
    'backend/app/repositories/tracking_repository.py',
    'backend/app/repositories/user_repository.py',
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for Create (my explicit blocks)
    # E.g. 
    #        if isinstance(data, BrandInternalCreate):
    #            internal_data = data
    #        else:
    #            internal_data = BrandInternalCreate(
    #                name=getattr(data, 'name', data.get('name') if isinstance(data, dict) else None),
    #                ...
    #            )
    pattern_create = r'(^[ \t]*)(if isinstance\((\w+), (\w+InternalCreate)\):\s*\n[ \t]+\w+\s*=\s*\w+\s*\n[ \t]+else:\s*\n[ \t]+(\w+)\s*=\s*\w+InternalCreate\([\s\S]*?\n[ \t]+\))'
    
    def replacer_create(match):
        indent = match.group(1)
        var_in = match.group(3)
        model_name = match.group(4)
        var_out = match.group(5)
        
        # We need to make sure model_validate supports from_attributes=True for dicts in earlier Pydantic v2 versions, but it does.
        # However, if data is already a dict, from_attributes=True is ignored and it uses keys.
        # Actually, let's just do:
        replacement = f"{indent}if isinstance({var_in}, dict):\n"
        replacement += f"{indent}    {var_out} = {model_name}.model_validate({var_in})\n"
        replacement += f"{indent}else:\n"
        replacement += f"{indent}    {var_out} = {model_name}.model_validate({var_in}, from_attributes=True)"
        return replacement

    content = re.sub(pattern_create, replacer_create, content, flags=re.MULTILINE)
    
    # Pattern for Update (my explicit blocks)
    #        if isinstance(data, BrandInternalUpdate):
    #            internal_data = data
    #        else:
    #            internal_data = BrandInternalUpdate()
    #            if isinstance(data, dict):
    #                if 'name' in data: internal_data.name = data['name']
    #                ...
    #            else:
    #                if 'name' in data.model_fields_set: internal_data.name = getattr(data, 'name')
    #                ...
    pattern_update = r'(^[ \t]*)(if isinstance\((\w+), (\w+InternalUpdate)\):\s*\n[ \t]+\w+\s*=\s*\w+\s*\n[ \t]+else:\s*\n[ \t]+(\w+)\s*=\s*\w+InternalUpdate\(\)[\s\S]*?(?=\n[ \t]+return|\n[ \t]+if|\n[ \t]+for|\n[ \t]+await|\n\n|\Z))'
    
    def replacer_update(match):
        indent = match.group(1)
        var_in = match.group(3)
        model_name = match.group(4)
        var_out = match.group(5)
        
        replacement = f"{indent}if isinstance({var_in}, dict):\n"
        replacement += f"{indent}    {var_out} = {model_name}.model_validate({var_in})\n"
        replacement += f"{indent}else:\n"
        replacement += f"{indent}    {var_out} = {model_name}.model_validate({var_in}.model_dump(exclude_unset=True))"
        return replacement

    content = re.sub(pattern_update, replacer_update, content, flags=re.MULTILINE)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
