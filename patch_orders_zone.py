import os
import re

filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add order_zone_id = None safely near the start of create_order
content = re.sub(r'(async def create_order.*?:\n)', r'\g<1>    order_zone_id = None\n', content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
