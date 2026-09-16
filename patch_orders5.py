import os
filepath = 'backend/app/routers/orders.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'new_sales = (bundle.sales_count if bundle.sales_count is not None else 0) + copies',
    'sales_c = bundle.get("salesCount", 0) if isinstance(bundle, dict) else getattr(bundle, "salesCount", getattr(bundle, "sales_count", 0))\n                    new_sales = (sales_c if sales_c is not None else 0) + copies'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
