import ast
import re

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

def build_explicit_update(var_in, var_out, model_name, indent):
    fields = models.get(model_name, [])
    res = f"{indent}{var_out} = {model_name}()\n"
    res += f"{indent}if isinstance({var_in}, dict):\n"
    for field in fields:
        res += f"{indent}    if '{field}' in {var_in}: {var_out}.{field} = {var_in}['{field}']\n"
    res += f"{indent}else:\n"
    for field in fields:
        res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
    return res

with open('backend/app/repositories/user_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()
update_block = build_explicit_update('update_data', 'internal_update', 'UserInternalUpdate', '        ')
content = content.replace('        return await self.storage.update(id, UserInternalUpdate(**update_data) if isinstance(update_data, dict) else update_data)', f'{update_block}\n        return await self.storage.update(id, internal_update)')
with open('backend/app/repositories/user_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
