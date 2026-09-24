import re

with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'isOnDuty: Optional[bool] = None' not in text:
    text = text.replace('isDeactivated: Optional[bool] = None', 'isDeactivated: Optional[bool] = None\n    isOnDuty: Optional[bool] = None')
    with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("ADDED isOnDuty to UserUpdate")
else:
    print("ALREADY EXISTS")
