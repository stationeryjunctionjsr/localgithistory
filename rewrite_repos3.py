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
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern_create = r'(^[ \t]*)(if isinstance\((\w+), dict\):\s*\n[ \t]+(\w+)\s*=\s*(\w+InternalCreate)\(\*\*\w+\)\s*\n[ \t]+elif not isinstance\(\w+, \w+InternalCreate\):\s*\n[ \t]+\w+\s*=\s*\w+InternalCreate\(\*\*\w+\.model_dump\(exclude_unset=True\)\)(?:\s*\n[ \t]+else:\s*\n[ \t]+\w+\s*=\s*\w+)?)'
    
    def replacer_create(match):
        indent = match.group(1)
        full_match = match.group(2)
        var_in = match.group(3)
        var_out = match.group(4)
        model_name = match.group(5)
        
        fields = models.get(model_name, [])
        mapping = []
        for field in fields:
            mapping.append(f"{indent}    {field}=getattr({var_in}, '{field}', {var_in}.get('{field}') if isinstance({var_in}, dict) else None)")
        
        replacement = f"{indent}if isinstance({var_in}, {model_name}):\n"
        replacement += f"{indent}    {var_out} = {var_in}\n"
        replacement += f"{indent}else:\n"
        replacement += f"{indent}    {var_out} = {model_name}(\n" + ",\n".join(mapping) + f"\n{indent}    )"
        return replacement

    content = re.sub(pattern_create, replacer_create, content, flags=re.MULTILINE)
    
    pattern_update = r'(^[ \t]*)(if isinstance\((\w+), dict\):\s*\n[ \t]+(\w+)\s*=\s*(\w+InternalUpdate)\(\*\*\w+\)\s*\n[ \t]+elif not isinstance\(\w+, \w+InternalUpdate\):\s*\n[ \t]+\w+\s*=\s*\w+InternalUpdate\(\*\*\w+\.model_dump\(exclude_unset=True\)\)(?:\s*\n[ \t]+else:\s*\n[ \t]+\w+\s*=\s*\w+)?)'
    
    def replacer_update(match):
        indent = match.group(1)
        full_match = match.group(2)
        var_in = match.group(3)
        var_out = match.group(4)
        model_name = match.group(5)
        
        fields = models.get(model_name, [])
        
        replacement = f"{indent}if isinstance({var_in}, {model_name}):\n"
        replacement += f"{indent}    {var_out} = {var_in}\n"
        replacement += f"{indent}else:\n"
        replacement += f"{indent}    {var_out} = {model_name}()\n"
        replacement += f"{indent}    if isinstance({var_in}, dict):\n"
        for field in fields:
            replacement += f"{indent}        if '{field}' in {var_in}: {var_out}.{field} = {var_in}['{field}']\n"
        replacement += f"{indent}    else:\n"
        for field in fields:
            replacement += f"{indent}        if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
        
        return replacement
        
    content = re.sub(pattern_update, replacer_update, content, flags=re.MULTILINE)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
