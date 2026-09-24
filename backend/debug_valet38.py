import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('    customer_zone_id = str(zone_doc.id)', '    customer_zone_id = str(zone_doc.id)\n    print(f"DEBUG: customer_zone_id={customer_zone_id}")')
text = text.replace('        if customer_zone_id not in valet_daily_zones:', '        print(f"DEBUG: checking if {customer_zone_id} in {valet_daily_zones}")\n        if customer_zone_id not in valet_daily_zones:')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
