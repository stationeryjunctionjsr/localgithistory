import os
filepath = 'backend/app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'class MySQLBundleDAO(MySQLFlatBaseDAO):',
    'class MySQLBundleDAO(MySQLFlatBaseDAO):\n    schema_cls = BundleResponse'
)
# And I must revert doc["items"] = ... to doc.items = ...
content = content.replace('doc["items"]', 'doc.items')
content = content.replace('(doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id")))', 'doc.external_id if getattr(doc, "external_id", None) is not None else doc.id')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
