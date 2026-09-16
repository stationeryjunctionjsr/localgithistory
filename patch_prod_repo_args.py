import os

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'subCategoryId=product_data.subCategory,',
    'subCategory=product_data.subCategory,'
)
content = content.replace(
    'variants=product_data.variantCombinations if product_data.variantCombinations is not None else [],',
    'variantCombinations=product_data.variantCombinations if product_data.variantCombinations is not None else [],'
)
content = content.replace(
    'if internal_create.variants:',
    'if internal_create.variantCombinations:'
)
content = content.replace(
    'for combo in internal_create.variants:',
    'for combo in internal_create.variantCombinations:'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
