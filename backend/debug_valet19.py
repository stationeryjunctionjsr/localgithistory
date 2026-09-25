import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('p_id = items[0].product_id', 'p_id = items[0].product_id')
text = text.replace('seller_id = prod.sellerId', 'seller_id = prod.sellers[0].sellerId if prod.sellers else None')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
