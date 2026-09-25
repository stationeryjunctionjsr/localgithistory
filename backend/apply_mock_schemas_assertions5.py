import os

filepath = 'tests/test_router_pydantic_refactor.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('assert valid.refreshId == "r1"', 'assert valid.refresh_id == "r1"')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
