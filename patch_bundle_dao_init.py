import os
filepath = 'backend/app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '            bool_api_keys=frozenset({"isActive"}),\\n            schema_cls=BundleResponse,\\n        )',
    '            bool_api_keys=frozenset({"isActive"}),\n        )'
)
content = content.replace(
    '            bool_api_keys=frozenset({"isActive"}),\n            schema_cls=BundleResponse,\n        )',
    '            bool_api_keys=frozenset({"isActive"}),\n        )'
)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
