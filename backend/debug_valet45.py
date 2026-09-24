with open('tests/test_returns_e2e.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if 'zone_storage = get_storage("deliveryZones")' in line:
        out.append(line)
        out.append('    all_zones = await zone_storage.findAll()\n')
        out.append('    zone_doc = None\n')
        out.append('    for z in all_zones:\n')
        out.append('        if "123456" in str(z.pincodes or ""):\n')
        out.append('            zone_doc = z\n')
        out.append('            break\n')
        out.append('    if not zone_doc:\n')
        out.append('        from app.models.daos_flat import DeliveryZoneInternalCreate\n')
        out.append('        zone_doc = await zone_storage.create(DeliveryZoneInternalCreate(name="Test Zone", pincodes=["123456"], isActive=True))\n')
        out.append('    zone_id = str(zone_doc.id)\n')
        skip = True
        continue
    
    if skip and 'zone_id = ' in line:
        skip = False
        continue
        
    if not skip:
        out.append(line)

with open('tests/test_returns_e2e.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
