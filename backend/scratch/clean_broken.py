import os
import re

for root, _, files in os.walk('backend/app/routers'):
    for file in files:
        if not file.endswith('.py'): continue
        filepath = os.path.join(root, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the broken lines
        content = re.sub(r'([A-Za-z_][A-Za-z0-9_]*\.([A-Za-z_][A-Za-z0-9_]*))\s*and\s*\"[A-Za-z0-9_]+\"\s*in\s*[A-Za-z0-9_]+\s*else\s*None\)*', r'\1', content)
        
        # fix specific leftovers
        content = content.replace('p.quantityTiers = (qty_coupon.quantityTiers)) or []', 'p.quantityTiers = qty_coupon.quantityTiers or []')
        content = content.replace('p.quantityTiers = (qty_coupon.quantityTiers) or []', 'p.quantityTiers = qty_coupon.quantityTiers or []')
        content = content.replace('p.quantityItemType = (qty_coupon.applicableItemType)) or "units"', 'p.quantityItemType = qty_coupon.applicableItemType or "units"')
        content = content.replace('p.quantityItemType = (qty_coupon.applicableItemType) or "units"', 'p.quantityItemType = qty_coupon.applicableItemType or "units"')
        content = content.replace('pid = item.product_id)))', 'pid = item.product_id')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
