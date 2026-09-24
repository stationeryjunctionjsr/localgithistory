import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})',
    'all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})\n      print(f"FIND_VALET all_valets={len(all_valets)}", file=sys.stderr)'
)
text = text.replace(
    'if not eligible_valets:\n          return None',
    'if not eligible_valets:\n          print("FIND_VALET no eligible valets", file=sys.stderr)\n          return None'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
