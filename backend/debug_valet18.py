import re

with open('app/repositories/product_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('getattr(p, "searchTags", getattr(p, "search_tags", None))', 'p.searchTags')

with open('app/repositories/product_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
