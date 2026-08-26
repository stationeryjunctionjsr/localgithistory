import os
import re

# Update payments.py
payments_file = "backend/app/routers/payments.py"
with open(payments_file, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"totalOverdue": total_dues,  # total credit not settled, irrespective of credit period', 
                          '"currentOverdue": total_overdue,')
# Make sure any other reference to totalOverdue in output is updated just in case
content = content.replace('"totalOverdue": total_dues,', '"currentOverdue": total_overdue,')
content = content.replace('"totalOverdue":', '"currentOverdue":')

with open(payments_file, "w", encoding="utf-8") as f:
    f.write(content)

# Update cart/page.tsx
cart_file = "frontend/src/app/customer/cart/page.tsx"
with open(cart_file, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("totalOverdue", "currentOverdue")
content = content.replace("Total overdue", "Current overdue")

with open(cart_file, "w", encoding="utf-8") as f:
    f.write(content)
