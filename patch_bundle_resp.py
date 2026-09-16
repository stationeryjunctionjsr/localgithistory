import os
filepath = 'backend/app/models/schemas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'class BundleResponse(BaseModel):',
    'class BundleResponse(BaseModel):\n    external_id: Optional[str] = None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
