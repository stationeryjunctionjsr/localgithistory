import re

with open('app/db/mysql_returnRequests_dao.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('out["valetAssignedAt"] = rm["valet_assigned_at"]', 'out["valetAssignedAt"] = rm["valet_assigned_at"].isoformat() + "Z" if rm["valet_assigned_at"] else None')

with open('app/db/mysql_returnRequests_dao.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
