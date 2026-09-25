import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'order_id = return_req.order_id',
    'order_id = return_req.order_id\n    import sys\n    print(f"FIND_VALET order_id={order_id}", file=sys.stderr)'
)
text = text.replace(
    'if not order:\n        return None',
    'if not order:\n        print("FIND_VALET no order", file=sys.stderr)\n        return None'
)
text = text.replace(
    'if not customer_pincode:\n        return None',
    'if not customer_pincode:\n        print("FIND_VALET no pincode", file=sys.stderr)\n        return None'
)

text = text.replace(
    'if not seller_id:\n            seller_id = order.seller_id',
    'if not seller_id:\n            seller_id = order.seller_id\n    print(f"FIND_VALET seller_id={seller_id}", file=sys.stderr)'
)

text = text.replace(
    'customer_zone_id = str(zone_doc.id) if zone_doc else None',
    'customer_zone_id = str(zone_doc.id) if zone_doc else None\n    print(f"FIND_VALET customer_zone_id={customer_zone_id}", file=sys.stderr)'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
