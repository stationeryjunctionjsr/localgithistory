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

models = {**get_model_fields('backend/app/models/daos.py'), **get_model_fields('backend/app/models/daos_flat.py')}

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

    # We need to find the instances of InternalCreate(**...) and replace them.
    # We will use regex to find the patterns.
    # The subagents used:
    # if isinstance(data, dict):
    #     internal_data = BrandInternalCreate(**data)
    # elif not isinstance(data, BrandInternalCreate):
    #     internal_data = BrandInternalCreate(**data.model_dump(exclude_unset=True))
    
    # We can match this whole block:
    # if isinstance\((\w+), dict\):\n\s+(\w+)\s*=\s*(\w+InternalCreate)\(\*\*\w+\)\n\s+elif not isinstance\(\w+, \w+InternalCreate\):\n\s+\w+\s*=\s*\w+InternalCreate\(\*\*\w+\.model_dump\(exclude_unset=True\)\)
    
    pattern_create = r'(if isinstance\((\w+), dict\):\s*\n\s+(\w+)\s*=\s*(\w+InternalCreate)\(\*\*\w+\)\s*\n\s+elif not isinstance\(\w+, \w+InternalCreate\):\s*\n\s+\w+\s*=\s*\w+InternalCreate\(\*\*\w+\.model_dump\(exclude_unset=True\)\))'
    
    def replacer_create(match):
        full_match = match.group(1)
        var_in = match.group(2)
        var_out = match.group(3)
        model_name = match.group(4)
        
        fields = models.get(model_name, [])
        mapping = []
        for field in fields:
            mapping.append(f"            {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
        
        replacement = f"        {var_out} = {model_name}(\n" + ",\n".join(mapping) + "\n        )"
        return replacement

    content = re.sub(pattern_create, replacer_create, content)
    
    # Do the same for Update
    pattern_update = r'(if isinstance\((\w+), dict\):\s*\n\s+(\w+)\s*=\s*(\w+InternalUpdate)\(\*\*\w+\)\s*\n\s+elif not isinstance\(\w+, \w+InternalUpdate\):\s*\n\s+\w+\s*=\s*\w+InternalUpdate\(\*\*\w+\.model_dump\(exclude_unset=True\)\))'
    
    def replacer_update(match):
        full_match = match.group(1)
        var_in = match.group(2)
        var_out = match.group(3)
        model_name = match.group(4)
        
        fields = models.get(model_name, [])
        
        replacement = f"        {var_out} = {model_name}()\n"
        replacement += f"        if isinstance({var_in}, dict):\n"
        for field in fields:
            replacement += f"            if '{field}' in {var_in}: {var_out}.{field} = {var_in}['{field}']\n"
        replacement += f"        else:\n"
        for field in fields:
            replacement += f"            if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = {var_in}.{field}\n"
        
        return replacement
        
    content = re.sub(pattern_update, replacer_update, content)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
