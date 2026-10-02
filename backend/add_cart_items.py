import re

file_path = "app/models/schemas.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("    price: Optional[float] = None", "    price: Optional[float] = None\n    cart_items: Optional[List[ItemSnippet]] = None")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Added cart_items to AnalyticsEventCreate")
