import os
filepath = 'backend/app/repositories/zone_seller_cache.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if pincode in (zone.pincodes or []):',
    'if pincode in (zone.get("pincodes", []) if isinstance(zone, dict) else (getattr(zone, "pincodes", []) or [])):'
)
content = content.replace(
    '_active_seller_cache[zone.id] = list(active)',
    '_active_seller_cache[zone.get("id") if isinstance(zone, dict) else zone.id] = list(active)'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
