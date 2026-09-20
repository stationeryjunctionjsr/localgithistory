import re

with open('schema.sql', 'r', encoding='utf-8') as f:
    text = f.read()

events_match = re.search(r'CREATE TABLE sj_events.*?;', text, re.DOTALL)
if events_match:
    print('sj_events:')
    print(events_match.group(0))

tracking_match = re.search(r'CREATE TABLE sj_tracking.*?;', text, re.DOTALL)
if tracking_match:
    print('sj_tracking:')
    print(tracking_match.group(0))
