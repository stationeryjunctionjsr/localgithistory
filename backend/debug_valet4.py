import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'seller_address = (seller[\'address\'] if \'address\' in seller else None) or {}',
    'seller_address = seller.address if hasattr(seller, "address") else None'
)
text = text.replace(
    'pincode = str((seller_address[\'zipCode\'] if \'zipCode\' in seller_address else None) or (seller_address[\'pincode\'] if \'pincode\' in seller_address else None) or \'\')',
    'pincode = str(seller_address.pincode if seller_address else "")'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
