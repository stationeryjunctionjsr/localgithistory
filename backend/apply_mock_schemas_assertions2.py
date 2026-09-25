import os
import re

filepath = 'tests/test_router_pydantic_refactor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any attribute access like obj.somethingCamel to obj.something_camel
replacements = {
    'tier.maxOrderValue': 'tier.max_order_value',
    'tier.commissionPct': 'tier.commission_pct',
    'slot.isFullDay': 'slot.is_full_day',
    'event.sessionId': 'event.session_id',
    'event.userId': 'event.user_id',
    'addr.zipCode': 'addr.zip_code',
    'req.sessionId': 'req.session_id',
    'req.refreshId': 'req.refresh_id',
}

for old, new in replacements.items():
    text = text.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
