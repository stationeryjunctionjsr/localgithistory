import re
with open('app/models/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
    campaign: Optional[str] = None
    device: Optional[Any] = None
    deviceType: Optional[str] = None
    deviceOsVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    deviceAppVersion: Optional[str] = None
'''

text = re.sub(
    r'    campaign: Optional\[str\] = None\n    device: Optional\[Any\] = None',
    replacement.strip('\n'),
    text
)

with open('app/models/schemas.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated schemas.py")
