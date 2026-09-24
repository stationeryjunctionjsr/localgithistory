import re

with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """class UserBase(BaseModel):
    isActive: Optional[bool] = None
    maxConcurrentOrders: Optional[int] = None"""

text = re.sub(r"class UserBase\(BaseModel\):\n    isActive: Optional\[bool\] = None", replacement, text)

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
