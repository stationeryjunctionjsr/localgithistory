import os

filepath = 'app/models/daos_flat.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

if 'from app.models.base import CamelBaseModel' not in text[:500]:
    text = 'from app.models.base import CamelBaseModel\n' + text

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
