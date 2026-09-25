import re

filepath = r"app\db\mysql_tracking_dao.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

for camel, snake in [("ipAddress", "ip_address"), ("testRunId", "test_run_id"), ("sessionId", "session_id"), ("userId", "user_id")]:
    text = text.replace(f"data.{camel}", f"data.{snake}")
    text = text.replace(f"existing.{camel}", f"existing.{snake}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
