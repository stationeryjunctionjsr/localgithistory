import os

filepath = 'backend/app/routers/categories.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('category.sub_categories', 'category.subCategories')
content = content.replace('category.minimum_quantity', 'category.minimumQuantity')
content = content.replace('category.is_active', 'category.isActive')
content = content.replace('category.show_in_mobile_homepage', 'category.showInMobileHomepage')
content = content.replace('category.is_returnable', 'category.isReturnable')
content = content.replace('category.category_tag', 'category.categoryTag')
content = content.replace('category.category_tags', 'category.categoryTags')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
