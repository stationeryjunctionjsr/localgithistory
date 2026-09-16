import os
filepath = 'backend/app/repositories/order_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'update_data.status == "out_for_delivery"',
    '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "out_for_delivery"'
)
content = content.replace(
    'update_data.shippedAt is None',
    '(update_data.get("shippedAt") if isinstance(update_data, dict) else update_data.shippedAt) is None'
)
content = content.replace(
    'update_data.shippedAt = datetime.now(timezone.utc).isoformat()',
    'if isinstance(update_data, dict): update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()\n        else: update_data.shippedAt = datetime.now(timezone.utc).isoformat()'
)

content = content.replace(
    'update_data.status == "delivered"',
    '(update_data.get("status") if isinstance(update_data, dict) else update_data.status) == "delivered"'
)
content = content.replace(
    'update_data.deliveredAt is None',
    '(update_data.get("deliveredAt") if isinstance(update_data, dict) else update_data.deliveredAt) is None'
)
content = content.replace(
    'update_data.deliveredAt = datetime.now(timezone.utc).isoformat()',
    'if isinstance(update_data, dict): update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()\n            else: update_data.deliveredAt = datetime.now(timezone.utc).isoformat()'
)
content = content.replace(
    'update_data.paymentStatus is None',
    '(update_data.get("paymentStatus") if isinstance(update_data, dict) else update_data.paymentStatus) is None'
)
content = content.replace(
    'update_data.paymentStatus = "paid"',
    'if isinstance(update_data, dict): update_data["paymentStatus"] = "paid"\n                    else: update_data.paymentStatus = "paid"'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
