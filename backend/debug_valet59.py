import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('now_iso = datetime.now(timezone.utc).isoformat() + "Z"', 'now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")')
text = text.replace('now_iso = now.isoformat() + "Z"', 'now_iso = now.strftime("%Y-%m-%d %H:%M:%S")')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
