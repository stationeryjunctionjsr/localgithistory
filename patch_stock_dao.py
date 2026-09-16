import os
filepath = 'backend/app/db/mysql_flat_daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

def replacer():
    # We will just rewrite the field accesses
    import re
    res = content
    res = res.replace('data.productId', 'data.get("productId") if isinstance(data, dict) else getattr(data, "productId", None)')
    res = res.replace('data.userId', 'data.get("userId") if isinstance(data, dict) else getattr(data, "userId", None)')
    res = res.replace('data.quantity', 'data.get("quantity") if isinstance(data, dict) else getattr(data, "quantity", None)')
    res = res.replace('data.status', 'data.get("status") if isinstance(data, dict) else getattr(data, "status", None)')
    res = res.replace('data.expiresAt', 'data.get("expiresAt") if isinstance(data, dict) else getattr(data, "expiresAt", None)')
    res = res.replace('if "expiresAt" in data:', 'if (isinstance(data, dict) and "expiresAt" in data) or hasattr(data, "expiresAt"):')
    return res

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(replacer())
