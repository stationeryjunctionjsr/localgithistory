import re

with open('app/db/mysql_returnRequests_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace my broken insert with the right one
text = text.replace(
    'INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason, declined_at) VALUES (:id, :v0, :v1, :v2)',
    'INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason) VALUES (:id, :v0, :v1)'
)

with open('app/db/mysql_returnRequests_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
