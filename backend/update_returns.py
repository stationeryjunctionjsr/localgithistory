with open('app/routers/returns.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_create = '''    created = await return_request_repository.create(
        {
            "orderId": request_data.orderId,
            "userId": current_user.id,
            "items": [i for i in request_data.items],
            "paymentMethod": request_data.paymentMethod,
            "upiPaymentScreenshot": screenshot_path,
            "notes": request_data.notes,
            "status": ReturnRequestStatus.PENDING.value,
            "deliveryCharge": delivery_charge_val,
        }
    )'''

new_create = '''    from app.models.daos import ReturnRequestInternalCreate
    created = await return_request_repository.create(
        ReturnRequestInternalCreate(
            orderId=request_data.orderId,
            userId=current_user.id,
            items=[i for i in request_data.items],
            paymentMethod=request_data.paymentMethod,
            upiPaymentScreenshot=screenshot_path,
            notes=request_data.notes,
            status=ReturnRequestStatus.PENDING.value,
            deliveryCharge=delivery_charge_val,
        )
    )'''

if old_create in text:
    text = text.replace(old_create, new_create)
else:
    print("Could not find returns create method")

with open('app/routers/returns.py', 'w', encoding='utf-8') as f:
    f.write(text)
