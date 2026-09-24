import re

with open('app/routers/returns.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'now_iso = datetime\.utcnow\(\)\.isoformat\(\) \+ "Z"', 'now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")', text)
text = re.sub(r'now_iso = datetime\.now\(timezone\.utc\)\.isoformat\(\) \+ "Z"', 'now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")', text)

# Just to be safe, replace ANY timezone import issues
text = "from datetime import timezone\n" + text

with open('app/routers/returns.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
