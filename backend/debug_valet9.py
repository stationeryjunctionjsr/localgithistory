import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'if not eligible_valets:\n          return None',
    'print(f"FIND_VALET eligible_valets={len(eligible_valets)}", file=sys.stderr)\n      if not eligible_valets:\n          return None'
)
text = text.replace(
    'if not zone_doc:\n          logger.warning(\'[ValetTimeout] Return %s: customer pincode %s not in any zone \u2014 cannot route\', return_req.id, customer_pincode)\n          return None',
    'if not zone_doc:\n          print("FIND_VALET no zone_doc!", file=sys.stderr)\n          logger.warning(\'[ValetTimeout] Return %s: customer pincode %s not in any zone \u2014 cannot route\', return_req.id, customer_pincode)\n          return None'
)
text = text.replace(
    'if not available_valets:\n          return None',
    'print(f"FIND_VALET available_valets={len(available_valets)}", file=sys.stderr)\n      if not available_valets:\n          return None'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
