import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'seller = await user_repository.findOne({\'role\': \'super_admin\'})',
    'all_users = await user_repository.findAll({})\n          print(f"FIND_VALET ALL_USERS={[u.role for u in all_users]}", file=sys.stderr)\n          seller = await user_repository.findOne({\'role\': \'super_admin\'})\n          print(f"FIND_VALET SUPER_ADMIN DB QUERY={seller}", file=sys.stderr)'
)
text = text.replace(
    'if not eligible_valets:\n          return None',
    'print(f"FIND_VALET eligible_valets={len(eligible_valets)}", file=sys.stderr)\n      if not eligible_valets:\n          return None'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
