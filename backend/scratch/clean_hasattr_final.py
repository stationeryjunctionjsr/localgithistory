import os, re
for root, _, files in os.walk('backend/app/routers'):
    for file in files:
        if not file.endswith('.py'): continue
        filepath = os.path.join(root, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix model_dump
        content = re.sub(r'(\w+)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*dict\(\1\)', r'\1', content)
        content = re.sub(r'(\w+)\.model_dump\(([^)]*)\)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*dict\(\1\)', r'\1.model_dump(\2)', content)
        content = re.sub(r'(\w+)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*(\w+)', r'\1', content)
        content = re.sub(r'(\w+)\.model_dump\(\)\s*if\s*hasattr\(\1,\s*[\'\"]model_dump[\'\"]\)\s*else\s*dict\(\1\)', r'\1.model_dump()', content)
        
        # specific ones
        content = content.replace('request.subscription.endpoint if hasattr(request.subscription, "endpoint") else (', 'request.subscription.endpoint if request.subscription.endpoint else (')
        content = content.replace('sub_payload = request.subscription.model_dump() if (has_web_subscription and hasattr(request.subscription, "model_dump")) else (request.subscription if has_web_subscription else None)', 'sub_payload = request.subscription.model_dump() if has_web_subscription else None')
        content = content.replace('p.images[0] if hasattr(p, "images") and p.images else (', 'p.images[0] if p.images else (')
        content = content.replace('if hasattr(order_data, "couponCode") and order_data.couponCode:', 'if getattr(order_data, "couponCode", None):')
        content = content.replace('if hasattr(order_data, "referralCode") and order_data.referralCode:', 'if getattr(order_data, "referralCode", None):')
        content = content.replace('elif hasattr(prod, "id"):', 'elif getattr(prod, "id", None):')
        content = content.replace('total = await user_repository.count(query) if hasattr(user_repository, "count") else len(users)', 'total = await user_repository.count(query)')
        content = content.replace('if hasattr(av_id, "id"):', 'if getattr(av_id, "id", None):')
        content = content.replace('if hasattr(perms, "serviceableZoneIds"):', 'if getattr(perms, "serviceableZoneIds", None):')
        content = content.replace('doc.date.strftime("%Y-%m-%d") if hasattr(doc.date, "strftime") else str(doc.date)[:10]', 'doc.date.strftime("%Y-%m-%d")')
        content = content.replace('item.product.id if hasattr(item.product, "id") else item.product', 'item.product.id')
        content = content.replace('[p.model_dump(by_alias=True) if hasattr(p, "model_dump") else p for p in payment_entries]', '[p.model_dump(by_alias=True) for p in payment_entries]')
        content = content.replace('product.model_dump(by_alias=True) if product and hasattr(product, "model_dump") else (product if product else {"_id": prod_id, "name": "Product not found"})', 'product.model_dump(by_alias=True) if product else {"_id": prod_id, "name": "Product not found"}')
        content = content.replace('[(e if hasattr(e, "model_dump") else e) for e in enriched] if enriched and hasattr(enriched[0], "model_dump") else enriched', '[e for e in enriched]')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print('Cleaned')
