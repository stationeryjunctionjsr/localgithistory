import re

with open('app/routers/orders.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the first one
text = text.replace('                    "createdAt": order.created_at.isoformat() if order.created_at else None,\n                },\n            }\n        )', '                    "createdAt": order.created_at.isoformat() if order.created_at else None,\n                })\n        )')

# Fix the second one
text = text.replace('                    "paymentMethod": payment.payment_method,\n                    "createdAt": payment.created_at.isoformat() if payment.created_at else None,\n                },\n            }\n        )', '                    "paymentMethod": payment.payment_method,\n                    "createdAt": payment.created_at.isoformat() if payment.created_at else None,\n                })\n        )')

# Fix the third one
text = text.replace('                                    "createdAt": sub.created_at.isoformat() if sub.created_at else None,\n                                },\n                            }\n                        )', '                                    "createdAt": sub.created_at.isoformat() if sub.created_at else None,\n                                })\n                        )')

with open('app/routers/orders.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
