import os

filepath = r"C:\Users\RESHAM DILAWARI\.gemini\antigravity\brain\d87d9ce7-79ea-4843-900e-eacac0995ba9\task.md"
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    text = text.replace('[/] NoSQL DB Refactoring', '[x] NoSQL DB Refactoring')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
