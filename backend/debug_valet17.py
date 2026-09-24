import re

with open('app/repositories/product_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('p.categoryTag', 'getattr(p, "categoryTag", getattr(p, "category_tag", None))')
text = text.replace('p.variantCombinations', 'getattr(p, "variantCombinations", getattr(p, "variant_combinations", None))')
text = text.replace('p.searchTags', 'getattr(p, "searchTags", getattr(p, "search_tags", None))')

with open('app/repositories/product_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
