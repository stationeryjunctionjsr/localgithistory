import os
import re

filepath = 'backend/app/repositories/product_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''    async def create(self, product_data: Any) -> Product:
        from app.models.daos import ProductInternalCreate
        if isinstance(product_data, dict):
            product_data.setdefault("mrp", 0.0)
            product_data.setdefault("price", 0.0)
            product_data.setdefault("category", "Uncategorized")
            product_data = ProductInternalCreate(**product_data)'''

content = content.replace(
    '    async def create(self, product_data: Any) -> Product:',
    replacement
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
