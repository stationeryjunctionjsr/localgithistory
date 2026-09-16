import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add order_zone_id = None at the top of create_order function
content = content.replace(
    'async def create_order(\n    order_data: OrderCreateRequest,\n    user_id: str = Depends(get_current_user_id),\n    db_session=Depends(get_db),\n):',
    'async def create_order(\n    order_data: OrderCreateRequest,\n    user_id: str = Depends(get_current_user_id),\n    db_session=Depends(get_db),\n):\n    order_zone_id = None'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
