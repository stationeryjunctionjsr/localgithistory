import os

filepath = 'tests/test_router_pydantic_refactor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('assert valid.userId == "u1"', 'assert valid.user_id == "u1"')
text = text.replace('Msg91WebhookPayloadSchema(Status="delivered")', 'Msg91WebhookPayloadSchema(status="delivered")')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
