import os

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'subCategoryId=product_data.subCategoryId,',
    'subCategoryId=product_data.subCategory,'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
