import re

with open('app/jobs/valet_timeout_job.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('    for v, load in valet_load:\n        if load < global_max:\n            return v', '    for v, load in valet_load:\n        print(f"DEBUG: checking load {load} < {global_max} for valet {v.id}")\n        if load < global_max:\n            return v')

with open('app/jobs/valet_timeout_job.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
