import os

filepath = 'app/models/schemas.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace 'stats: Optional[AdStats] = Field(default_factory=AdStats)'
# With the flat fields
flat_fields = '''    stat_impressions: Optional[int] = 0
    stat_clicks: Optional[int] = 0
    stat_leads: Optional[int] = 0
    stat_purchases: Optional[int] = 0
    stat_add_to_cart: Optional[int] = 0
    stat_conversions: Optional[int] = 0
    stat_conversion_value: Optional[float] = 0.0
    stat_ctr: Optional[float] = 0.0
    stat_cvr: Optional[float] = 0.0'''

text = text.replace('    stats: Optional[AdStats] = Field(default_factory=AdStats)', flat_fields)
text = text.replace('    stats: Optional[AdStats] = None', flat_fields)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
