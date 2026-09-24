import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add print statements inside the _find_next_available_valet_for_return
print_code = """
    print("CUSTOMER PINCODE:", customer_pincode)
    print("REQUIRED ZONE ID:", customer_zone_id)
    print("ALL VALETS:", [str(v.id) for v in all_valets])
    print("AVAILABLE DOCS:", len(availability_docs))
"""

text = text.replace(
    'avail_map = {str(doc.valet_id): doc for doc in availability_docs if doc.valet_id}',
    'avail_map = {str(doc.valet_id): doc for doc in availability_docs if doc.valet_id}\n    print("CUSTOMER PINCODE:", customer_pincode)\n    print("REQUIRED ZONE ID:", customer_zone_id)\n    print("ALL VALETS:", [str(v.id) for v in all_valets])\n    print("AVAILABLE VALETS DOCS (from DB):", list(avail_map.keys()))'
)
text = text.replace(
    'if not (customer_zone_id in valet_daily_zones or "*" in valet_daily_zones):',
    'print("VALET ZONES:", vid, valet_daily_zones)\n            if not (customer_zone_id in valet_daily_zones or "*" in valet_daily_zones):'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
