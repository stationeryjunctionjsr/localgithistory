import re

with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add couponMode to CouponBase if not exists
if 'couponMode: Optional[str]' not in text:
    text = text.replace('applicableItemType: Optional[str] = None  # units | cases', 'applicableItemType: Optional[str] = None  # units | cases\n    couponMode: Optional[str] = None')

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
