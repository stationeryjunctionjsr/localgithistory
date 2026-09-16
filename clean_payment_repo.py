import os
import re

filepath = 'backend/app/repositories/payment_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# p is now a Payment model, so it has paymentId
# replace (p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None)) with getattr(p, "paymentId", getattr(p, "payment_id", None))

pattern1 = r'\(p\.get\("paymentId"\)\s*if\s*isinstance\(p,\s*dict\)\s*else\s*getattr\(p,\s*"paymentId",\s*None\)\)'
content = re.sub(pattern1, 'getattr(p, "paymentId", getattr(p, "payment_id", None))', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
