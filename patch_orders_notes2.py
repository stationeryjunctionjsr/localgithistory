import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'else order_data.notes,',
    'else (order_data.notes or ""),'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
