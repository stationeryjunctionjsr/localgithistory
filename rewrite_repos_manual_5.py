import ast
import re

def get_model_fields(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    models = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    fields.append(item.target.id)
            models[node.name] = fields
    return models

models = {**get_model_fields('backend/app/models/daos.py'), **get_model_fields('backend/app/models/daos_flat.py'), **get_model_fields('backend/app/models/schemas.py')}

def build_explicit_update(var_in, var_out, model_name, indent):
    fields = models.get(model_name, [])
    res = f"{indent}{var_out} = {model_name}()\n"
    res += f"{indent}if isinstance({var_in}, dict):\n"
    if not fields: res += f"{indent}    pass\n"
    for field in fields:
        res += f"{indent}    if '{field}' in {var_in}: {var_out}.{field} = {var_in}['{field}']\n"
    res += f"{indent}else:\n"
    if not fields: res += f"{indent}    pass\n"
    for field in fields:
        res += f"{indent}    if '{field}' in {var_in}.model_fields_set: {var_out}.{field} = getattr({var_in}, '{field}')\n"
    return res

with open('backend/app/repositories/user_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()
# We need to replace the bad block with the good one
bad_block = '''        internal_update = UserInternalUpdate()
        if isinstance(update_data, dict):
        else:

        return await self.storage.update(id, internal_update)'''
good_block = build_explicit_update('update_data', 'internal_update', 'UserInternalUpdate', '        ') + '\n        return await self.storage.update(id, internal_update)'
content = content.replace(bad_block, good_block)
with open('backend/app/repositories/user_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
