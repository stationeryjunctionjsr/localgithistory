import os
filepath = 'backend/app/db/mysql_bundle_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('doc.items', 'doc["items"]')
content = content.replace('doc["items"] = await self._fetch_products((doc["external_id"] if doc["external_id"] is not None else doc["id"]))', 'doc["items"] = await self._fetch_products((doc.get("external_id") if doc.get("external_id") is not None else doc.get("_id", doc.get("id"))))')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
