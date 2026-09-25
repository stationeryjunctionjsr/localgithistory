import os
import re

filepath = 'app/models/banner.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('class Banner(BaseModel):', 'from app.models.base import CamelBaseModel\nclass Banner(CamelBaseModel):')

# Remove all hardcoded aliases because CamelBaseModel handles it natively
text = re.sub(r",\s*alias='[^']+'", "", text)
text = re.sub(r"alias='[^']+'", "", text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
