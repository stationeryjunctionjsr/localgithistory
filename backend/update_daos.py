import os

filepath = 'app/models/daos.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace properties in BannerChildrenData
# It likely has userSegments and visibilityRules
old = '''class BannerChildrenData(BaseModel):
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[Dict]] = None'''

new = '''from app.models.base import CamelBaseModel

class BannerChildrenData(CamelBaseModel):
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[Dict]] = None'''

text = text.replace(old, new)
# Try more relaxed replace if spacing is off
text = text.replace('userSegments:', 'user_segments:')
text = text.replace('visibilityRules:', 'visibility_rules:')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
