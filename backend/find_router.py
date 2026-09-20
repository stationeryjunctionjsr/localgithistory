import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '/events' in line:
        for j in range(max(0, i-2), min(len(lines), i+60)):
            print(f"{j}: {lines[j].strip()}")
        break
