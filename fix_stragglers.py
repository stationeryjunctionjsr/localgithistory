import re

with open('backend/app/models/tracking.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('product_ids: List[Any]', 'product_ids: List[str]')
with open('backend/app/models/tracking.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/app/models/wishlist.py', 'r', encoding='utf-8') as f:
    content = f.read()
if 'from app.models.daos import WishlistItemInternal' not in content:
    content = 'from app.models.daos import WishlistItemInternal\n' + content
content = content.replace('items: List[Any]', 'items: List[WishlistItemInternal]')
with open('backend/app/models/wishlist.py', 'w', encoding='utf-8') as f:
    f.write(content)

