import re

filepath = 'frontend/src/utils/syncCartWishlist.ts'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace empty/warn wishlist catch block
content = content.replace('logger.error("Failed to sync wishlist item", e);', 'logger.error("Failed to sync wishlist item", e);\n        toast.warn("Some wishlist items could not be synced");')

# Replace the overarching catches to also toast
content = re.sub(r'logger\.error\("Cart sync failed entirely", e\);', 'logger.error("Sync failed entirely", e);\n    toast.error("Failed to synchronize your saved items.");', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated syncCartWishlist.ts")
