import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '"userId": user_for_payment.user_id,',
    '"userId": str(user_for_payment.user_id),'
)
content = content.replace(
    '"orderDate": order.created_at,',
    '"orderDate": order.created_at if isinstance(order.created_at, str) else str(order.created_at),'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
