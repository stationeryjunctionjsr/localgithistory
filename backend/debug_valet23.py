import re

with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure NotificationInternalCreate is imported
if 'from app.models.daos import NotificationInternalCreate' not in text:
    text = text.replace('from app.models.daos import OrderInternalCreate, OrderInternalUpdate, SubOrderInternalCreate', 'from app.models.daos import OrderInternalCreate, OrderInternalUpdate, SubOrderInternalCreate, NotificationInternalCreate')

# Replace dicts with NotificationInternalCreate
text = text.replace('await notification_repository.create(\n            {\n                "userId":', 'import uuid\n        await notification_repository.create(\n            NotificationInternalCreate(**{\n                "_id": str(uuid.uuid4()),\n                "userId":')
text = text.replace('await notification_repository.create(\n                            {\n                                "userId":', 'import uuid\n                        await notification_repository.create(\n                            NotificationInternalCreate(**{\n                                "_id": str(uuid.uuid4()),\n                                "userId":')

# Close the parens correctly
text = text.replace('                      "userId": order.user,\n                  }\n              }\n          )', '                      "userId": order.user,\n                  }\n              })\n          )')
text = text.replace('                      "amount": (payment.total_amount if payment.total_amount is not None else 0),\n                  }\n              }\n          )', '                      "amount": (payment.total_amount if payment.total_amount is not None else 0),\n                  }\n              })\n          )')
text = text.replace('                                      "amount": grp_total,\n                                  }\n                              }\n                          )', '                                      "amount": grp_total,\n                                  }\n                              })\n                          )')

# Also replace data with metadata since NotificationInternalCreate uses metadata
text = text.replace('"data": {', '"metadata": {')

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
