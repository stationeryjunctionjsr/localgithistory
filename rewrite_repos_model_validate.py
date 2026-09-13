import glob
import re

for fpath in glob.glob('backend/app/repositories/*.py'):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for subagents Create:
    # if isinstance(data, dict):
    #     internal_data = BrandInternalCreate(**data)
    # elif not isinstance(data, BrandInternalCreate):
    #     internal_data = BrandInternalCreate(**data.model_dump(exclude_unset=True))
    
    # We will just replace Model(**dict) with Model.model_validate(dict)
    # and Model(**obj.model_dump(...)) with Model.model_validate(obj.model_dump(...))
    
    # Wait, for Create, we can just use model_validate(obj, from_attributes=True)
    # But since they already wrote the if/else block, let's just do text replacement!
    
    # Let's just find and replace Model(**...) everywhere!
    # \b(\w+Internal(?:Create|Update))\(\*\*(.*?)\) -> \1.model_validate(\2)
    # But wait, model_validate doesn't support **kwargs! 
    # If the subagents wrote BrandInternalCreate(**data), we change it to BrandInternalCreate.model_validate(data).
    
    def replacer(match):
        model_name = match.group(1)
        arg = match.group(2)
        return f"{model_name}.model_validate({arg})"

    content = re.sub(r'\b(\w+Internal(?:Create|Update))\(\*\*(.*?)\)', replacer, content)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
