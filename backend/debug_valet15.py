import re

with open('app/repositories/recommendation_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('p.subCategory or', 'p.sub_category or')

with open('app/repositories/recommendation_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
