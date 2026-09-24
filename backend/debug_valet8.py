import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})\n      print(f"FIND_VALET all_valets={len(all_valets)}", file=sys.stderr)',
    'all_valets = await user_repository.findAll({\'role\': \'valet\', \'isOnDuty\': True})'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
