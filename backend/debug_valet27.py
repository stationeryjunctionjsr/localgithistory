import re

with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix closing braces for NotificationInternalCreate
text = re.sub(r'(\s*)\},\n\s*\}\n\s*\)', r'\1}\n            })\n        )', text)

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
