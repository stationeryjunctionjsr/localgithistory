with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

old_snippet = '''class ItemSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    productId: Optional[str] = Field(default=None, validation_alias=AliasChoices("productId", "product_id"))
    product: Optional[str] = None
    quantity: Optional[int] = None
    sellAsCase: Optional[bool] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    name: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None
    variantAttributes: Optional['VariantAttributes'] = Field(default=None, validation_alias=AliasChoices("variantAttributes", "variant_attributes"))'''

new_snippet = '''class ItemSnippet(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra='forbid')
    productId: Optional[str] = Field(default=None, validation_alias=AliasChoices("productId", "product_id"))
    product: Optional[str] = None
    quantity: Optional[int] = None
    sellAsCase: Optional[bool] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    name: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None
    bundleId: Optional[str] = Field(default=None, validation_alias=AliasChoices("bundleId", "bundle_id"))
    bundleName: Optional[str] = Field(default=None, validation_alias=AliasChoices("bundleName", "bundle_name"))
    variantAttributes: Optional['VariantAttributes'] = Field(default=None, validation_alias=AliasChoices("variantAttributes", "variant_attributes"))'''

if old_snippet in text:
    text = text.replace(old_snippet, new_snippet)
else:
    print("Could not find exactly matching ItemSnippet")

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
