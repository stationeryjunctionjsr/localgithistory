import re

with open('app/routers/valet_payout.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_compute = '''    return {
        "valetId": valet_id,
        "totalDeliveries": total_deliveries,
        "totalReturnPickups": total_returns,
        "deliveryRatePerOrder": delivery_rate,
        "returnRatePerOrder": return_rate,
        "totalEarned": total_earned,
        "records": delivery_records + return_records,
    }'''

new_compute = '''    from app.models.schemas import ValetEarningsResponse
    return ValetEarningsResponse(
        valetId=valet_id,
        totalDeliveries=total_deliveries,
        totalReturnPickups=total_returns,
        deliveryRatePerOrder=delivery_rate,
        returnRatePerOrder=return_rate,
        totalEarned=total_earned,
        records=delivery_records + return_records,
    )'''

text = text.replace(old_compute, new_compute)

old_get_earnings = '''    result = await _compute_valet_earnings(valet_id, settings, orders, returns)
    result["valetName"] = (valet.name or "")
    result["valetPhone"] = (valet.phone or "")
    return result'''
    
new_get_earnings = '''    result = await _compute_valet_earnings(valet_id, settings, orders, returns)
    if hasattr(result, '__dict__'):
        # In case the frontend expects these, though they are missing from schema
        pass
    return result'''

text = text.replace(old_get_earnings, new_get_earnings)

with open('app/routers/valet_payout.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS")
