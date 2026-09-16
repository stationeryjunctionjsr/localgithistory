import os

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'variants=product_data.variantCombinations if getattr(product_data, "variantCombinations", None) is not None else [],\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n',
    'variants=getattr(product_data, "variants", []),\\n            variantAttributes=getattr(product_data, "variantAttributes", []),\\n'
).replace('\\\\n', '\\n')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
