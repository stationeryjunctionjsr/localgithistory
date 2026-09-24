import re

with open('tests/test_returns_e2e.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """    zone_storage = get_storage("deliveryZones")
    all_zones = await zone_storage.findAll()
    zone_doc = None
    for z in all_zones:
        if "123456" in str(z.pincodes or ""):
            zone_doc = z
            break
    if not zone_doc:
        zone_doc = await zone_storage.create(DeliveryZoneInternalCreate(name="Test Zone", pincodes=["123456"], isActive=True))
    zone_id = str(zone_doc.id)
    print("DEBUG: test_returns_e2e created Valet with zone_id=", zone_id)"""

text = re.sub(r'    zone_storage = get_storage\("deliveryZones"\)\n    zone_doc = await zone_storage\.findOne\(\{"pincodes": "123456"\}\)\n    if not zone_doc:\n        zone_doc = await zone_storage\.create\(\{"pincodes": "123456", "name": "Test Zone", "isActive": True\}\)\n    zone_id = str\(zone_doc\.id\)\n    print\("DEBUG: test_returns_e2e created Valet with zone_id=", zone_id\)', replacement, text)

with open('tests/test_returns_e2e.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
