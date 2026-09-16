import os
filepath = 'backend/app/repositories/order_repository.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'update_data: OrderInternalUpdate',
    'update_data: Any'
)
content = content.replace(
    'update_data.status',
    '(update_data.get("status") if isinstance(update_data, dict) else update_data.status)'
)
content = content.replace(
    'update_data.shippedAt is None',
    '(update_data.get("shippedAt") if isinstance(update_data, dict) else getattr(update_data, "shippedAt", None)) is None'
)
content = content.replace(
    'update_data.shippedAt = ',
    'if isinstance(update_data, dict): update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()\n        elif not isinstance(update_data, dict): update_data.shippedAt = '
)
content = content.replace(
    'update_data.deliveredAt is None',
    '(update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt", None)) is None'
)
content = content.replace(
    'update_data.deliveredAt = ',
    'if isinstance(update_data, dict): update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()\n            elif not isinstance(update_data, dict): update_data.deliveredAt = '
)
content = content.replace(
    'update_data.paymentStatus is None',
    '(update_data.get("paymentStatus") if isinstance(update_data, dict) else getattr(update_data, "paymentStatus", None)) is None'
)
content = content.replace(
    'update_data.paymentStatus = ',
    'if isinstance(update_data, dict): update_data["paymentStatus"] = "paid"\n                    elif not isinstance(update_data, dict): update_data.paymentStatus = '
)
content = content.replace(
    'update_data.codPaymentReceived is None',
    '(update_data.get("codPaymentReceived") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceived", None)) is None'
)
content = content.replace(
    'update_data.codPaymentReceived = ',
    'if isinstance(update_data, dict): update_data["codPaymentReceived"] = True\n                elif not isinstance(update_data, dict): update_data.codPaymentReceived = '
)
content = content.replace(
    'update_data.codPaymentReceivedAt is None',
    '(update_data.get("codPaymentReceivedAt") if isinstance(update_data, dict) else getattr(update_data, "codPaymentReceivedAt", None)) is None'
)
content = content.replace(
    'update_data.codPaymentReceivedAt = ',
    'if isinstance(update_data, dict): update_data["codPaymentReceivedAt"] = datetime.now(timezone.utc).isoformat()\n                elif not isinstance(update_data, dict): update_data.codPaymentReceivedAt = '
)
content = content.replace(
    'update_data.turnaroundHours = ',
    'if isinstance(update_data, dict): update_data["turnaroundHours"] = round(hours, 2)\n                    elif not isinstance(update_data, dict): update_data.turnaroundHours = '
)
content = content.replace(
    'update_data.cancelledAt is None',
    '(update_data.get("cancelledAt") if isinstance(update_data, dict) else getattr(update_data, "cancelledAt", None)) is None'
)
content = content.replace(
    'update_data.cancelledAt = ',
    'if isinstance(update_data, dict): update_data["cancelledAt"] = datetime.now(timezone.utc).isoformat()\n        elif not isinstance(update_data, dict): update_data.cancelledAt = '
)
# Make sure we don't accidentally do it where update_data.deliveredAt string was accessed:
content = content.replace(
    'datetime.fromisoformat(update_data.deliveredAt',
    'datetime.fromisoformat((update_data.get("deliveredAt") if isinstance(update_data, dict) else getattr(update_data, "deliveredAt"))'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
