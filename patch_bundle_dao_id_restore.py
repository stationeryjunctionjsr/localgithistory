import os
filepath = 'backend/app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('doc.id', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')
# Now fix cases where it might have doubled up
content = content.replace('((doc.external_id if getattr(doc, "external_id", None) is not None else doc.id))', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')
content = content.replace('(doc.external_id if getattr(doc, "external_id", None) is not None else (doc.external_id if getattr(doc, "external_id", None) is not None else doc.id))', '(doc.external_id if getattr(doc, "external_id", None) is not None else doc.id)')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
