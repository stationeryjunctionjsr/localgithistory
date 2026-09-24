import re

with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = "from app.models.daos import NotificationInternalCreate\n" + text

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
