with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('device: Optional[Any] = None', 'device: Optional[Dict[str, str]] = None')

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)
