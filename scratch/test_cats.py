import urllib.request
import json

try:
    url = "http://localhost:8000/api/categories/public"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    for category in data:
        name = category.get("name")
        sub_cats = category.get("subCategories")
        category_tags = category.get("categoryTags")
        print(f"ID: {category.get('_id')} | Name: {name} | Tags: {category_tags} | Subcategories: {sub_cats}")
except Exception as e:
    print("Error:", e)
