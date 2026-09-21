with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"createdAt": order.created_at,', '"createdAt": order.created_at.isoformat() if order.created_at else None,')

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
