import os

filepath = 'backend/app/routers/categories.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('category.categoryTag', 'category.category_tag')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
