import re

filepath = 'frontend/src/utils/syncCartWishlist.ts'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = "import { logger } from '@/utils/logger';\nimport { toast } from 'react-toastify';\n" + content

new_content = new_content.replace(
    "catch {\n        // silently skip items that fail\n      }",
    'catch (e) {\n        logger.error("Failed to sync cart item", e);\n        toast.warn("Some cart items could not be synced");\n      }'
)
new_content = new_content.replace(
    "catch {\n    // ignore\n  }", 'catch (e) {\n    logger.error("Cart sync failed entirely", e);\n  }'
)
new_content = new_content.replace(
    "catch {\n        // silently skip\n      }",
    'catch (e) {\n        logger.error("Failed to sync wishlist item", e);\n      }'
)
new_content = new_content.replace("catch {}", 'catch (e) { logger.warn("Failed to parse legacy cart/wishlist", e); }')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
