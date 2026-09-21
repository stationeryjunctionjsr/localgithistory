import os

files = ["app/routers/orders.py", "app/routers/payments.py", "app/routers/returns.py"]
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text = text.replace('id=str(uuid.uuid4()),', '_id=str(uuid.uuid4()),')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
