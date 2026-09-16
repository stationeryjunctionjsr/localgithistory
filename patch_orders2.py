import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'variantAttributes=item.variant_attributes',
    'variantAttributes=getattr(item, "variantAttributes", getattr(item, "variant_attributes", None))'
)
content = content.replace(
    'variantAttributes=item.variantAttributes',
    'variantAttributes=getattr(item, "variantAttributes", getattr(item, "variant_attributes", None))'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
