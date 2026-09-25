import os

filepath = 'tests/test_router_pydantic_refactor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update EXEMPT_CALLERS
text = text.replace('"min_versions",', '"min_versions",\n    "candidate",\n    "payload",\n    "result",')

# 2. Update Assertions from camelCase to snake_case
text = text.replace('assert valid.sessionId == "s_123"', 'assert valid.session_id == "s_123"')
text = text.replace('assert webhook.resolved_status == "delivered"', 'assert webhook.resolved_status == "delivered"') # No change
text = text.replace('assert req.userId == "u_1"', 'assert req.user_id == "u_1"')
text = text.replace('assert slot.isUrgent is True', 'assert slot.is_urgent is True')
text = text.replace('assert tier.minOrderValue == 0.0', 'assert tier.min_order_value == 0.0')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
