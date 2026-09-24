import re

with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add missing fields to _build_query_conditions
new_conditions = '''        if 'approvalStatus' in query:
            where_clauses.append('approval_status = :approvalStatus')
            params['approvalStatus'] = query['approvalStatus']
        if 'isActive' in query:
            where_clauses.append('is_active = :isActive')
            params['isActive'] = 1 if query['isActive'] else 0
        if 'allowed_ids' in query:'''

text = text.replace("        if 'allowed_ids' in query:", new_conditions)

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
