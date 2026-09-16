import os
filepath = 'backend/tests/test_bundle_recommendations.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'assert "bundles" in data',
    'assert isinstance(data, list)'
)
content = content.replace(
    'assert len(data["bundles"]) >= 1',
    'assert len(data) >= 1'
)
content = content.replace(
    'data["bundles"][0]',
    'data[0]'
)
content = content.replace(
    'data["bundles"][-1]',
    'data[-1]'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
