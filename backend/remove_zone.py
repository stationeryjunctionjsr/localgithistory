import re

filepath = 'app/db/mysql_banner_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace in SELECT
content = content.replace(', position, zone_ids, created_at', ', position, created_at')
# Replace in INSERT
content = content.replace(', position,\n                        zone_ids,\n                        created_at', ', position,\n                        created_at')
content = content.replace(':target_audience, :position,\n                        :zone_ids,\n                        :created_at', ':target_audience, :position,\n                        :created_at')
content = content.replace('"zone_ids": json.dumps(data.zone_ids) if data.zone_ids else None,', '')

# Replace in UPDATE
content = content.replace('position = :position,\n                        zone_ids = :zone_ids,\n                        updated_at = :updated_at', 'position = :position,\n                        updated_at = :updated_at')
content = content.replace('"zone_ids": json.dumps(merged["zoneIds"]) if merged["zoneIds"] else None,', '')
content = content.replace('"zone_ids": json.dumps(merged["zone_ids"]) if merged.get("zone_ids") else None,', '')
content = content.replace('"zone_ids": json.dumps(merged["zone_ids"]) if "zone_ids" in merged and merged["zone_ids"] else None,', '')
content = re.sub(r'"zone_ids":[^,]+,', '', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
