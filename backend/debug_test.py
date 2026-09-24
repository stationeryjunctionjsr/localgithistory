import re

with open('tests/test_returns_e2e.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'assert len(eligibility["eligibleItems"]) > 0, "No items eligible for return!"',
    'assert len(eligibility["eligibleItems"]) > 0, f"No items eligible for return! Reason: {eligibility.get(\'reason\')}"'
)

with open('tests/test_returns_e2e.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
