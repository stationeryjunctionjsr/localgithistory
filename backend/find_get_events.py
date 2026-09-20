import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '@router.get' in line and '/events' in line:
        for j in range(max(0, i-5), min(len(lines), i+30)):
            print(f"{j}: {lines[j].strip()}")
