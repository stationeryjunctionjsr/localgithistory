import re
with open('app/db/mysql_user_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'if \'isSellerAdmin\' in query:\n            where_clauses.append(\'is_seller_admin = :isSellerAdmin\')\n            params[\'isSellerAdmin\'] = 1 if query[\'isSellerAdmin\'] else 0',
    'if \'isSellerAdmin\' in query:\n            where_clauses.append(\'is_seller_admin = :isSellerAdmin\')\n            params[\'isSellerAdmin\'] = 1 if query[\'isSellerAdmin\'] else 0\n        if \'isOnDuty\' in query:\n            where_clauses.append(\'is_on_duty = :isOnDuty\')\n            params[\'isOnDuty\'] = 1 if query[\'isOnDuty\'] else 0'
)

with open('app/db/mysql_user_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
