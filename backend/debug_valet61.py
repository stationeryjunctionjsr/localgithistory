import re

with open('app/db/mysql_returnRequests_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('sj_return_request_valet_declines', 'sj_return_valet_declines')
# Note: I also need to check if the columns are right! 
# The original INSERT was: INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason) VALUES (:id, :v0, :v1)
# Wait! My new insert added declined_at:
# INSERT INTO sj_return_valet_declines (parent_id, valet_id, reason, declined_at) VALUES (:id, :v0, :v1, :v2)
# Is declined_at actually in the table?

with open('app/db/mysql_returnRequests_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
