import re

filepath = r"app\repositories\user_repository.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Remove device_id and msg91_token
text = re.sub(r'\s*device_id=getattr\(user_data, \'device_id\', None\),', '', text)
text = re.sub(r'\s*msg91_token=getattr\(user_data, \'msg91_token\', None\),', '', text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)

