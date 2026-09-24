import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'seller = await user_repository.findOne({\'role\': \'super_admin\'})',
    'seller = await user_repository.findOne({\'role\': \'super_admin\'})\n          print(f"FIND_VALET SUPER_ADMIN DB QUERY={seller}", file=sys.stderr)\n          all_users = await user_repository.findAll({})\n          print(f"ALL_USERS={[ (u.email, u.role) for u in all_users]}", file=sys.stderr)'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
