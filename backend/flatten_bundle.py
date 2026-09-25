import os
import re

filepath = 'app/models/bundle.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('class BundleItem(BaseModel):', 'from app.models.base import CamelBaseModel\nclass BundleItem(CamelBaseModel):')
text = text.replace('productId: Optional[str] = Field(default=None, alias="product_id")', 'product_id: Optional[str] = None')

text = text.replace('class Bundle(BaseModel):', 'class Bundle(CamelBaseModel):')
text = text.replace('id: str = Field(default="", alias="_id")', 'id: str = Field(default="", alias="_id")')
text = text.replace('discountPercentage: Optional[float] = None', 'discount_percentage: Optional[float] = None')
text = text.replace('isActive: bool = True', 'is_active: bool = True')
text = text.replace('salesCount: Optional[int] = 0', 'sales_count: Optional[int] = 0')
text = text.replace('createdAt: Optional[str] = None', 'created_at: Optional[str] = None')
text = text.replace('updatedAt: Optional[str] = None', 'updated_at: Optional[str] = None')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
