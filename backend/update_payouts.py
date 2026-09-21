with open('app/routers/seller_payouts.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_payout_1 = '''    payout_doc = {
        "sellerId": data.sellerId,
        "sellerName": seller.company_name or seller.name or "",
        "amount": data.amount,
        "periodStart": data.periodStart,
        "periodEnd": data.periodEnd,
        "status": "paid",
        "notes": data.notes,
        "subOrderIds": data.subOrderIds or [],
        "createdBy": str(current_user.id),
        "paidAt": now,
        "createdAt": now,
    }

    storage = _payout_storage()
    created = await storage.create(payout_doc)'''

new_payout_1 = '''    from app.models.daos import SellerPayoutInternalCreate
    storage = _payout_storage()
    created = await storage.create(
        SellerPayoutInternalCreate(
            sellerId=data.sellerId,
            sellerName=seller.company_name or seller.name or "",
            amount=data.amount,
            periodStart=data.periodStart,
            periodEnd=data.periodEnd,
            status="paid",
            notes=data.notes,
            subOrderIds=data.subOrderIds or [],
            createdBy=str(current_user.id),
            paidAt=now,
            createdAt=now,
        )
    )'''
text = text.replace(old_payout_1, new_payout_1)

old_payout_2 = '''    payout_doc = {
        "sellerId": seller_id,
        "sellerName": seller.company_name or seller.name or "",
        "amount": round(total_amount, 2),
        "status": "paid",
        "notes": "Bulk settlement of all realized sub-orders",
        "subOrderIds": sub_order_ids,
        "createdBy": str(current_user.id),
        "paidAt": now,
        "createdAt": now,
    }

    storage = _payout_storage()
    created = await storage.create(payout_doc)'''

new_payout_2 = '''    from app.models.daos import SellerPayoutInternalCreate
    storage = _payout_storage()
    created = await storage.create(
        SellerPayoutInternalCreate(
            sellerId=seller_id,
            sellerName=seller.company_name or seller.name or "",
            amount=round(total_amount, 2),
            status="paid",
            notes="Bulk settlement of all realized sub-orders",
            subOrderIds=sub_order_ids,
            createdBy=str(current_user.id),
            paidAt=now,
            createdAt=now,
        )
    )'''
text = text.replace(old_payout_2, new_payout_2)

with open('app/routers/seller_payouts.py', 'w', encoding='utf-8') as f:
    f.write(text)
