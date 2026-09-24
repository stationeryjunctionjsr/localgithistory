import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'if not seller:\n          return None',
    'print(f"FIND_VALET seller={seller}", file=sys.stderr)\n      if not seller:\n          print("FIND_VALET no seller found!", file=sys.stderr)\n          return None'
)

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
