import re

with open('backend/app/models/core.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Delete DictCompatibleModel class entirely
pattern = r'class DictCompatibleModel\(BaseModel\):.*'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open('backend/app/models/core.py', 'w', encoding='utf-8') as f:
    f.write(content)
