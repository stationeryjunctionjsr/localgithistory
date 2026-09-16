import os

filepath = 'backend/app/routers/categories.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('cat.categoryTag = tag or ""', 'cat.category_tag = tag or ""')
content = content.replace('cat.categoryTags = [tag] if tag else []', 'cat.category_tags = [tag] if tag else []')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
