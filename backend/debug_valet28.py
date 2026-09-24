import re

with open('app/routers/returns.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('metametadata={', 'metadata={')

with open('app/routers/returns.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
