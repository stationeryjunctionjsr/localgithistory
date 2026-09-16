import os
filepath = 'backend/app/repositories/payment_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'p.paymentId',
    '(p.get("paymentId") if isinstance(p, dict) else getattr(p, "paymentId", None))'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
