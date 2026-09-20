import re

with open('tests/test_analytics_and_tracking.py', 'r', encoding='utf-8') as f:
    text = f.read()
    
matches = re.findall(r'client\.(?:get|post)\(r?\"(.*?)\"', text)
for m in set(matches):
    print(m)
