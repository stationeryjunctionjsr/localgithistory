import os
import re

filepath = 'app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

old_item = '''class BundleItemInternal(BaseModel):
    productId: str
    productName: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discountPrice: Optional[float] = None'''

new_item = '''from app.models.base import CamelBaseModel
class BundleItemInternal(CamelBaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discount_price: Optional[float] = None'''

text = text.replace(old_item, new_item)

old_create = '''class BundleInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: str
    items: Optional[List[BundleItemInternal]] = []
    products: Optional[List[BundleItemInternal]] = []
    salesCount: Optional[int] = 0
    price: float
    isActive: bool = True
    isSystem: bool = False'''

new_create = '''class BundleInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = None
    name: str
    items: Optional[List[BundleItemInternal]] = []
    products: Optional[List[BundleItemInternal]] = []
    sales_count: Optional[int] = 0
    price: float
    is_active: bool = True
    is_system: bool = False'''

text = text.replace(old_create, new_create)

old_update = '''class BundleInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    externalId: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    items: Optional[List[BundleItemInternal]] = None
    price: Optional[float] = None
    isActive: Optional[bool] = None
    salesCount: Optional[int] = None
    updatedAt: Optional[Any] = None'''

new_update = '''class BundleInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid')
    external_id: Optional[str] = None
    name: Optional[str] = None
    items: Optional[List[BundleItemInternal]] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    sales_count: Optional[int] = None
    updated_at: Optional[Any] = None'''

text = text.replace(old_update, new_update)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
