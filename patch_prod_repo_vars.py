import os

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'variantCombinations=product_data.variantCombinations if product_data.variantCombinations is not None else [],',
    'variants=product_data.variantCombinations if getattr(product_data, "variantCombinations", None) is not None else [],\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n'
)
content = content.replace(
    'if internal_create.variantCombinations:',
    'if internal_create.variants:'
)
content = content.replace(
    'for combo in internal_create.variantCombinations:',
    'for combo in internal_create.variants:'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
