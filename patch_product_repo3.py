import os
import re
filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'p.subCategory': 'p.sub_category',
    'p.productId': 'p.product_id',
    'p.mrpPerCase': 'p.mrp_per_case',
    'p.quantityPerCase': 'p.quantity_per_case',
    'p.variantAttributes': 'p.variant_attributes',
    'p.isExclusive': 'p.is_exclusive',
    'product.searchTags': 'product.searchTags', # added this manually
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
