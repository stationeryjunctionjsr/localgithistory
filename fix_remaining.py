import re

def fix_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, new in replacements.items():
        if i-1 < len(lines):
            lines[i-1] = new + '\n'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# backend/app/services/email_service.py:189
fix_file('backend/app/services/email_service.py', {
    189: '            prod_name = (item["product"] if "product" in item else {})["name"] if "name" in (item["product"] if "product" in item else {}) else "Product"'
})

# backend/app/services/push_notification_service.py
fix_file('backend/app/services/push_notification_service.py', {
    127: '                user_map = {str(u["_id"]): u for u in chunk_users if "_id" in u}',
    135: '                user_map = {str(u["_id"]): u for u in chunk_users if "_id" in u}',
    348: '            order["_id"] if "_id" in order else None,',
    374: '            order["_id"] if "_id" in order else None,',
    400: '            order["_id"] if "_id" in order else None,',
    420: '            <= datetime.fromisoformat((o["createdAt"] if "createdAt" in o else "").replace("Z", "+00:00"))',
    438: '            order["_id"] if "_id" in order else None,',
    458: '            <= datetime.fromisoformat((o["createdAt"] if "createdAt" in o else "").replace("Z", "+00:00"))'
})

# backend/app/utils/email_otp.py
fix_file('backend/app/utils/email_otp.py', {
    124: '    record = email_otp_store[email.lower()] if email.lower() in email_otp_store else None',
    128: '    # record = email_otp_store[email.lower()] if email.lower() in email_otp_store else None',
    142: '    device = devices[device_key] if device_key in devices else None',
    146: '    # device = devices[device_key] if device_key in devices else None'
})

# backend/app/utils/file_storage.py
fix_file('backend/app/utils/file_storage.py', {
    94: '        if (doc["_id"] if "_id" in doc else None) != value and (doc["id"] if "id" in doc else None) != value:',
    99: '        if (doc["_id"] if "_id" in doc else None) != value and (doc["id"] if "id" in doc else None) != value:',
    110: '        if str(doc["_id"] if "_id" in doc else None) not in allowed_ids_strs and str(doc["id"] if "id" in doc else None) not in allowed_ids_strs:',
    111: '            # removed duplicate'
})

# backend/app/utils/invoice_generator.py
fix_file('backend/app/utils/invoice_generator.py', {
    153: '            ["Invoice Number:", order["orderNumber"] if "orderNumber" in order else (order["_id"] if "_id" in order else "N/A")],',
    186: '    seller_state = ((seller_info["address"] if "address" in seller_info else {})["state"] if "state" in (seller_info["address"] if "address" in seller_info else {}) else "").upper().strip()',
    187: '    # removed',
    190: '    buyer_state = ((order["shippingAddress"] if "shippingAddress" in order else {})["state"] if "state" in (order["shippingAddress"] if "shippingAddress" in order else {}) else "").upper().strip()',
    191: '    # removed',
    207: '        single_unit_price = item["singleUnitPrice"] if "singleUnitPrice" in item else (item["price"] if "price" in item else 0)',
    208: '        num_units = item["numberOfSingleUnits"] if "numberOfSingleUnits" in item else (item["quantity"] if "quantity" in item else 0)',
    286: '    if (order["discount"] if "discount" in order else 0) > 0:',
    289: '    if (order["shipping"] if "shipping" in order else 0) > 0:',
    296: '    if (order["discount"] if "discount" in order else 0) > 0:',
    299: '    if (order["shipping"] if "shipping" in order else 0) > 0:'
})

# backend/app/utils/otp.py
fix_file('backend/app/utils/otp.py', {
    287: '    record = otp_store[user_key] if user_key in otp_store else None',
    291: '    # record = otp_store[user_key] if user_key in otp_store else None',
    305: '    device = devices[device_key] if device_key in devices else None',
    309: '    # device = devices[device_key] if device_key in devices else None',
    470: '    user_record = otp_store[user_key] if user_key in otp_store else None',
    472: '    # user_record = otp_store[user_key] if user_key in otp_store else None',
    477: '    device = user_record["devices"][device_key] if device_key in user_record["devices"] else None',
    482: '    # device = user_record["devices"][device_key] if device_key in user_record["devices"] else None'
})

# backend/app/utils/product_variations.py
fix_file('backend/app/utils/product_variations.py', {
    62: '    if not (product["variations"] if "variations" in product else None) or len(product["variations"] if "variations" in product else []) == 0:',
    64: '        # removed',
    71: '        selected_option = selected_variations[variation["name"] if "name" in variation else None] if (variation["name"] if "name" in variation else None) in selected_variations else None if selected_variations else None'
})
