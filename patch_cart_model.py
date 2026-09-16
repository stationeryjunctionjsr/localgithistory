import os
filepath = 'backend/app/models/cart.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'class Cart(BaseModel):',
    'class Cart(BaseModel):\n    id: Optional[str] = Field(default=None, alias="_id")'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
