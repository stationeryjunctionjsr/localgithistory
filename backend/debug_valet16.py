import re

with open('app/repositories/recommendation_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('p.subCategory', 'p.sub_category')

with open('app/repositories/recommendation_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
