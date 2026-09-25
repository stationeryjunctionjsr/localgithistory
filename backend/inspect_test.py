import re

with open('tests/test_delivery_zones_and_checkout.py', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i, line in enumerate(lines):
    if '{' in line and ('isActive' in line or 'pincodes' in line or 'applicableRoles' in line or '_id' in line):
        print(f"Line {i+1}: {line}")
