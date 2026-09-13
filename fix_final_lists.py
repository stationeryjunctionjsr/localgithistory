import re

# 1. Product (backend/app/models/product.py)
with open('backend/app/models/product.py', 'r', encoding='utf-8') as f:
    content = f.read()
if 'from app.models.schemas import' not in content:
    content = content.replace('from pydantic import BaseModel', 'from pydantic import BaseModel\nfrom app.models.schemas import VariantOption, UserSnippet')
content = content.replace('variant_attributes: List[Any]', 'variant_attributes: List[str]')
content = content.replace('sellers: List[Any]', 'sellers: List[UserSnippet]')
content = content.replace('variants: List[Any]', 'variants: List[VariantOption]')
with open('backend/app/models/product.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Orders (backend/app/models/order.py)
with open('backend/app/models/order.py', 'r', encoding='utf-8') as f:
    content = f.read()

valet_model = '''
class ValetDeclineHistoryEntry(BaseModel):
    valetId: str
    reason: Optional[str] = None
'''
if 'ValetDeclineHistoryEntry' not in content:
    content = content.replace('class OrderBase(BaseModel):', valet_model + '\nclass OrderBase(BaseModel):')

content = content.replace('valet_decline_history: List[Any]', 'valet_decline_history: List[ValetDeclineHistoryEntry]')
content = content.replace('valetDeclineHistory: Optional[List[Any]]', 'valetDeclineHistory: Optional[List[ValetDeclineHistoryEntry]]')
with open('backend/app/models/order.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 3. Cart, Wishlist, Bundle items (backend/app/models/daos.py)
with open('backend/app/models/daos.py', 'r', encoding='utf-8') as f:
    content = f.read()

wishlist_model = '''
class WishlistItemInternal(BaseModel):
    product: str
'''
bundle_model = '''
class BundleItemInternal(BaseModel):
    productId: str
    productName: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    discountPrice: Optional[float] = None
'''

if 'WishlistItemInternal' not in content:
    content = content.replace('class WishlistInternalCreate(BaseModel):', wishlist_model + '\nclass WishlistInternalCreate(BaseModel):')
if 'BundleItemInternal' not in content:
    content = content.replace('class BundleInternalCreate(BaseModel):', bundle_model + '\nclass BundleInternalCreate(BaseModel):')

content = re.sub(r'(class WishlistInternal(?:Create|Update)\(BaseModel\):[\s\S]*?)items: (?:Optional\[)?List\[Any\](?:\])?( = \[\]| = None)?', r'\1items: Optional[List[WishlistItemInternal]]\2', content)
content = re.sub(r'(class BundleInternal(?:Create|Update)\(BaseModel\):[\s\S]*?)items: (?:Optional\[)?List\[Any\](?:\])?( = \[\]| = None)?', r'\1items: Optional[List[BundleItemInternal]]\2', content)

with open('backend/app/models/daos.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 4. Duplicate Legacy Code (backend/app/models/schemas.py)
with open('backend/app/models/schemas.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Delete class OrderCreateInternal entirely
pattern = r'class OrderCreateInternal\(BaseModel\):.*?(?=\n\nclass|\Z)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open('backend/app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(content)

