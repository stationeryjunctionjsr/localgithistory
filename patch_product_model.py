import os
filepath = 'backend/app/models/product.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")',
    '    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")\n    searchTags: Optional[List[str]] = None\n    resolvedCollectionNames: Optional[List[str]] = None\n    previouslyBought: Optional[bool] = None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
