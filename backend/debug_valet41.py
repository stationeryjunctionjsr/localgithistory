import re

with open('tests/test_returns_e2e.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = """    zone_storage = get_storage("deliveryZones")
    zone_doc = await zone_storage.findOne({"pincodes": "123456"})
    if not zone_doc:
        zone_doc = await zone_storage.create({"pincodes": "123456", "name": "Test Zone", "isActive": True})
    zone_id = str(zone_doc.id)
    print("DEBUG: test_returns_e2e created Valet with zone_id=", zone_id)"""

text = text.replace('    zone_storage = get_storage("deliveryZones")\n    zone_doc = await zone_storage.findOne({"pincodes": "123456"})\n    if not zone_doc:\n        zone_doc = await zone_storage.create({"pincodes": "123456", "name": "Test Zone", "isActive": True})\n    zone_id = str(zone_doc.id)', replacement)

with open('tests/test_returns_e2e.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("SUCCESS")
