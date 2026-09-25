import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: ReturnRequestInternal camelCase
text = text.replace('return_req.order_id', 'return_req.order_id')
text = text.replace('return_req.seller_id', 'return_req.sellerId')
text = text.replace('return_req.delivery_slot_id', 'return_req.deliverySlotId')
text = text.replace('return_req.product_id', 'return_req.product_id')

# Fix 2: Product sellerId
text = text.replace('prod.sellerId if hasattr(prod, \'sellerId\') else None', 'prod.sellers[0].sellerId if prod.sellers else None')
text = text.replace('prod.sellerId if hasattr(prod, "sellerId") else None', 'prod.sellers[0].sellerId if prod.sellers else None')
text = text.replace('seller_id = prod.seller_id if hasattr(prod, \'seller_id\') else None', 'seller_id = prod.sellers[0].sellerId if prod.sellers else None')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
