import os

filepath = 'backend/app/routers/categories.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('category.subCategories', 'category.sub_categories')
content = content.replace('category.minimumQuantity', 'category.minimum_quantity')
content = content.replace('category.isActive', 'category.is_active')
content = content.replace('category.showInMobileHomepage', 'category.show_in_mobile_homepage')
content = content.replace('category.isReturnable', 'category.is_returnable')
content = content.replace('category.categoryTags', 'category.category_tags')
content = content.replace('cat.subCategories', 'cat.sub_categories')
content = content.replace('cat.minimumQuantity', 'cat.minimum_quantity')
content = content.replace('cat.isActive', 'cat.is_active')
content = content.replace('cat.showInMobileHomepage', 'cat.show_in_mobile_homepage')
content = content.replace('cat.isReturnable', 'cat.is_returnable')
content = content.replace('cat.categoryTags', 'cat.category_tags')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
