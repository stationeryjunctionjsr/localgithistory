import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('str(r.assignedValet or \'\')', 'str(getattr(r, "valetId", getattr(r, "assignedValet", "")))')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
