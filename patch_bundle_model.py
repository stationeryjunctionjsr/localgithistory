import os

filepath = 'backend/app/models/bundle.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '    id: str = Field(default="", alias="_id")',
    '''    id: str = Field(default="", alias="_id")
    name: str = ""
    description: Optional[str] = None
    price: float = 0.0
    discountPercentage: Optional[float] = None
    isActive: bool = True
    salesCount: Optional[int] = 0
    items: List[Any] = []
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    external_id: Optional[str] = None'''
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
