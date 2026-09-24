import re

with open('app/models/order.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the injected fields with camelCase
new_fields = '''
    user: Optional[str] = None
    orderNumber: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    orderType: Optional[str] = None
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    shippingAddress: Optional['OrderAddress'] = None
    billingAddress: Optional['OrderAddress'] = None
    notes: Optional[str] = None
    printedBill: Optional[bool] = None
    isUrgentDelivery: Optional[bool] = None
    items: Optional[List['OrderItem']] = None
'''

old_fields_regex = re.compile(r'    user: Optional\[str\] = None\n    order_number: Optional\[str\].*?items: Optional\[List\[\'OrderItem\'\]\] = None\n', re.DOTALL)

text = old_fields_regex.sub(new_fields[1:], text)

with open('app/models/order.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS replace camelcase")
