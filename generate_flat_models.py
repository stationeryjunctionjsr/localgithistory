import re

with open('backend/app/db/mysql_flat_daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

classes = re.findall(r'class (MySQL[a-zA-Z0-9_]+DAO):', content)
models_code = "from pydantic import BaseModel, ConfigDict\nfrom typing import Any, Optional, Dict, List\n\n"

for cls in classes:
    entity = cls.replace('MySQL', '').replace('DAO', '')
    
    # Extract the block for this class
    start = content.find(f'class {cls}:')
    end = content.find('class MySQL', start + 10)
    if end == -1: end = len(content)
    block = content[start:end]
    
    # Find all data.xyz and merged.xyz
    fields = set()
    for m in re.finditer(r'(?:data|merged)\.([a-zA-Z0-9_]+)', block):
        fields.add(m.group(1))
        
    models_code += f"class {entity}InternalCreate(BaseModel):\n"
    models_code += f"    model_config = ConfigDict(extra='ignore')\n"
    if not fields:
        models_code += "    pass\n"
    for field in sorted(fields):
        models_code += f"    {field}: Optional[Any] = None\n"
    models_code += "\n"
    
    models_code += f"class {entity}InternalUpdate(BaseModel):\n"
    models_code += f"    model_config = ConfigDict(extra='ignore')\n"
    if not fields:
        models_code += "    pass\n"
    for field in sorted(fields):
        models_code += f"    {field}: Optional[Any] = None\n"
    models_code += "\n"

with open('backend/app/models/daos_flat.py', 'w', encoding='utf-8') as f:
    f.write(models_code)
print("Models generated in daos_flat.py")
