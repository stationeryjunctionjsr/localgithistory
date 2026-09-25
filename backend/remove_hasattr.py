import re

with open('app/routers/valet_payout.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_code = '''    if hasattr(result, '__dict__'):
        # In case the frontend expects these, though they are missing from schema
        pass
    return result'''
new_code = '''    return result'''

text = text.replace(old_code, new_code)
with open('app/routers/valet_payout.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
