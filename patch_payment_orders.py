import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '"userId": current_user.id,',
    '"userId": str(current_user.id),'
)
content = content.replace(
    '"orderDate": datetime.now(timezone.utc),',
    '"orderDate": datetime.now(timezone.utc).isoformat(),'
)
# Just in case current_user.id is used elsewhere nearby
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
