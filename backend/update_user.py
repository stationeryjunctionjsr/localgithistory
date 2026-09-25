import os

filepath = r"app\models\user.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('phone: str = ""', 'phone: Optional[str] = ""')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
