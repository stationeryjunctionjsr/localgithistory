import re

with open('schema.sql', 'r', encoding='utf-8') as f:
    text = f.read()

events = re.search(r'CREATE TABLE (IF NOT EXISTS )?sj_events\s*\((.*?)\)\s*ENGINE', text, re.DOTALL | re.IGNORECASE)
tracking = re.search(r'CREATE TABLE (IF NOT EXISTS )?sj_tracking\s*\((.*?)\)\s*ENGINE', text, re.DOTALL | re.IGNORECASE)

if events:
    print('sj_events columns:\n' + events.group(2))
if tracking:
    print('sj_tracking columns:\n' + tracking.group(2))
